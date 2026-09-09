from src.jobs.load_models_job import load_models
from src.jobs.refresh_session_job import clear_session
from src.jobs.bm25_chat_builder_job import build_bm25_index


async def run_jobs():
    await load_models()
    clear_session()
    build_bm25_index()
