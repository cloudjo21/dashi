import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from dashi.model.api import api as model_api
from dashi.pl_model.api import api as plm_api
from dashi.vector.api import api as vec_api
from dashi.evaluate.api import api as eval_api
from dashi.contents.api import api as contents_api

app = FastAPI()

app.include_router(model_api)
app.include_router(plm_api)
app.include_router(vec_api)
app.include_router(eval_api)
app.include_router(contents_api)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    uvicorn.run(app, log_level="info")