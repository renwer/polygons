from fastapi import FastAPI
from redis import Redis

from app.api.endpoints import router
from app.config.settings import settings

app = FastAPI()
app.include_router(router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.API_HOST, port=settings.API_PORT)
