from __future__ import annotations
import base64
import json
import logging
import secrets
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import httpx
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from src.core.configs import (
    BASKET_DB,
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URI,
)
from src.services.db.db import get_db

logger = logging.getLogger(__name__)

authRouter = APIRouter(tags=["auth"])

# Default scopes required by Plum / Gmail integration
DEFAULT_GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
    "email",
    "profile",
    "openid",
]

# Ensure TTL and uniqueness indexes on the auth_tickets collection
try:
    _db = get_db(BASKET_DB)
    _db.auth_tickets.create_index("created_at", expireAfterSeconds=180)
    _db.auth_tickets.create_index("ticket_id", unique=True)
except Exception as _idx_err:
    logger.warning("Could not initialize auth_tickets indexes: %s", _idx_err)


def parse_state_payload(state: Optional[str]) -> Dict[str, Any]:
    """Safely decode and parse base64 or JSON state parameter."""
    if not state:
        return {}
    try:
        decoded = base64.b64decode(state).decode("utf-8")
        return json.loads(decoded)
    except Exception:
        try:
            return json.loads(state)
        except Exception:
            return {"raw": state}


class TicketRedeemRequest(BaseModel):
    ticket_id: str


@authRouter.get("/user/auth/callback")
@authRouter.get("/auth/callback")
async def google_auth_callback(
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    error_description: Optional[str] = Query(None),
) -> RedirectResponse:
    """
    Central Google OAuth Callback handler for Basket and all Fruit applications.
    Receives authorization code from Google, exchanges it for tokens,
    and redirects to the target fruit with a single-use handoff ticket.
    """
    state_data = parse_state_payload(state)
    fruit = str(state_data.get("fruit", "plum")).lower()

    # Determine default fallback redirect per fruit
    if fruit == "plum":
        cancel_redirect = "https://plum.jam/signin?warning=google_auth_cancelled"
        failure_redirect = "https://plum.jam/signin?error=auth_failed"
    else:
        cancel_redirect = f"https://{fruit}.jam/?warning=google_auth_cancelled"
        failure_redirect = f"https://{fruit}.jam/?error=auth_failed"

    # Handle user cancellation or Google authorization error
    if error:
        logger.warning("Google OAuth error received: error=%s, description=%s", error, error_description)
        return RedirectResponse(url=cancel_redirect, status_code=302)

    if not code:
        logger.warning("Google OAuth callback received without code")
        return RedirectResponse(url=failure_redirect, status_code=302)

    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        logger.error("Missing Google OAuth credentials in Basket configuration")
        return RedirectResponse(url=failure_redirect, status_code=302)

    # 1. Exchange authorization code with Google for tokens
    token_url = "https://oauth2.googleapis.com/token"
    token_payload = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            token_resp = await client.post(token_url, data=token_payload)

            if token_resp.status_code != 200:
                logger.error("Google token exchange failed [%d]: %s", token_resp.status_code, token_resp.text)
                return RedirectResponse(url=f"{failure_redirect}&reason=token_exchange_failed", status_code=302)

            token_data = token_resp.json()
            access_token = token_data.get("access_token")
            if not access_token:
                logger.error("No access_token found in Google token response: %s", token_data)
                return RedirectResponse(url=f"{failure_redirect}&reason=no_access_token", status_code=302)

            # 2. Fetch User Profile
            userinfo_resp = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )

            if userinfo_resp.status_code != 200:
                logger.error("Google userinfo fetch failed [%d]: %s", userinfo_resp.status_code, userinfo_resp.text)
                return RedirectResponse(url=f"{failure_redirect}&reason=userinfo_failed", status_code=302)

            user_info = userinfo_resp.json()

    except Exception as exc:
        logger.exception("Exception during Google OAuth exchange: %s", exc)
        return RedirectResponse(url=f"{failure_redirect}&reason=internal_error", status_code=302)

    # 3. Store single-use handoff ticket in MongoDB
    expires_in = token_data.get("expires_in")
    expiry_date = int(time.time() * 1000) + (expires_in * 1000) if expires_in else None

    ticket_id = f"ticket_{secrets.token_urlsafe(32)}"
    ticket_doc = {
        "ticket_id": ticket_id,
        "fruit": fruit,
        "action": state_data.get("action", "login"),
        "tokens": {
            "access_token": access_token,
            "refresh_token": token_data.get("refresh_token"),
            "id_token": token_data.get("id_token"),
            "expires_in": expires_in,
            "expiry_date": expiry_date,
        },
        "userInfo": user_info,
        "stateData": state_data,
        "created_at": datetime.now(timezone.utc),
    }

    try:
        db = get_db(BASKET_DB)
        db.auth_tickets.insert_one(ticket_doc)
        logger.info("Successfully created OAuth handoff ticket %s for fruit=%s, user=%s", ticket_id, fruit, user_info.get("email"))
    except Exception as exc:
        logger.exception("Failed to insert auth ticket into MongoDB: %s", exc)
        return RedirectResponse(url=f"{failure_redirect}&reason=db_error", status_code=302)

    # 4. Redirect browser to target Fruit handoff endpoint
    if fruit == "plum":
        handoff_url = f"https://api.plum.jam/user/auth/handoff?ticket={ticket_id}"
    else:
        handoff_url = f"https://api.{fruit}.jam/user/auth/handoff?ticket={ticket_id}"

    return RedirectResponse(url=handoff_url, status_code=302)


@authRouter.post("/auth/ticket/redeem")
async def redeem_ticket_post(req: TicketRedeemRequest) -> Dict[str, Any]:
    """Atomically redeem and delete an auth ticket (POST)."""
    return _redeem_ticket(req.ticket_id)


@authRouter.get("/auth/ticket/{ticket_id}")
async def redeem_ticket_get(ticket_id: str) -> Dict[str, Any]:
    """Atomically redeem and delete an auth ticket (GET)."""
    return _redeem_ticket(ticket_id)


def _redeem_ticket(ticket_id: str) -> Dict[str, Any]:
    if not ticket_id:
        raise HTTPException(status_code=400, detail="Ticket ID is required")

    db = get_db(BASKET_DB)
    ticket_doc = db.auth_tickets.find_one_and_delete({"ticket_id": ticket_id})

    if not ticket_doc:
        raise HTTPException(status_code=404, detail="Invalid or expired authentication ticket")

    ticket_doc.pop("_id", None)
    return {
        "success": True,
        "ticket": ticket_doc,
    }


@authRouter.get("/auth/url")
async def get_google_auth_url(
    fruit: str = "plum",
    action: str = "login",
    user_email: Optional[str] = None,
    target_mailbox: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate the standard Google OAuth URL for any Fruit application.
    """
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="GOOGLE_CLIENT_ID not configured")

    state_obj = {
        "fruit": fruit,
        "action": action,
        "userEmail": user_email or "",
        "targetMailbox": target_mailbox or "",
        "timestamp": int(time.time() * 1000),
    }
    state_b64 = base64.b64encode(json.dumps(state_obj).encode("utf-8")).decode("utf-8")

    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(DEFAULT_GOOGLE_SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "state": state_b64,
    }

    if target_mailbox:
        params["login_hint"] = target_mailbox

    from urllib.parse import urlencode
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"

    return {
        "success": True,
        "auth_url": auth_url,
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "state": state_obj,
    }

