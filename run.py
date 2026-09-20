import uvicorn

from src.core.configs import BASKET_HOST, BASKET_PORT, PRODUCTION

if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host=BASKET_HOST,
        port=BASKET_PORT,
        reload=False,
    )