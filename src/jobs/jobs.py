from src.jobs.load_models_job import load_models
from src.jobs.refresh_session_job import clear_session

async def run_jobs():
    await load_models()
    clear_session()