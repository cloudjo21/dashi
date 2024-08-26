import uvicorn
from fastapi import FastAPI

from dashi.feature.serving.api import api as feature_api


app = FastAPI()

app.include_router(feature_api)


if __name__ == "__main__":
    uvicorn.run(app, log_level="info")
