from src.jobs.load_models_job import load_models
from src.jobs.refresh_session_job import clear_session
from src.services.context.tiered_context import tiered_context

async def run_jobs():
    await load_models()
    await clear_session()
    await tiered_context.sync_all_fruits_startup()
