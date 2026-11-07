from fastapi import FastAPI

from backend import config

app = FastAPI(title=config.APP_NAME, version=config.APP_VERSION)


@app.get("/")
def read_root() -> dict[str, str]:
    return {"name": config.APP_NAME, "version": config.APP_VERSION, "status": "ok"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.app:app", host=config.HOST, port=config.PORT)
