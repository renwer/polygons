import pydantic
from pydantic import BaseModel


@pydantic.dataclasses.dataclass
class PointRequestPayload(BaseModel):
    bottom_left: tuple
    upper_right: tuple
    n: int
