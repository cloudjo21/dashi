import uvicorn
from fastapi import FastAPI

from dashi.evaluate.api import api

app = FastAPI()

app.include_router(api)

if __name__ == "__main__":
    uvicorn.run(app, log_level="info")