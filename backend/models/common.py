from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict


class PersistenceModel(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
        populate_by_name=True,
    )

    def to_mongo(self) -> dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True,)

    @classmethod
    def from_mongo(cls, document: dict[str, Any]):
        return cls.model_validate(document)


def mongo_datetime(value: datetime | None) -> datetime | None:
    return value
