from pydantic import BaseModel
from typing import Optional


class DeployResponse(BaseModel):
    status_code: int
    model_output_path: Optional[str]
    error_message: Optional[str] = None
