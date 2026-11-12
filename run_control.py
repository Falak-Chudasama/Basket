import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "src.control.server:app",
        host="127.0.0.1",
        port=10020,
        reload=False,
    )

