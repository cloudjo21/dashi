import numpy as np

from dataclasses import dataclass
from enum import Enum
from pydantic import BaseModel
from typing import Dict, List, Optional


class ContentsTaskInfo(BaseModel):
    entity_type: str
    domain_name: str

class DomainInfo(BaseModel):
    domain: str
    stat_type: str
    snapshot: str
    task_info: Optional[ContentsTaskInfo] = None

class ValueInfo(BaseModel):
    feature_type: str
    value: float