import logging

from pydantic import BaseModel
from typing import Optional

from tunip.logger import init_logging_handler


LOGGER = init_logging_handler(name="dashi", level=logging.INFO)


class DashiResponse(BaseModel):
    status_code: int = 200
    status_message: Optional[str]
