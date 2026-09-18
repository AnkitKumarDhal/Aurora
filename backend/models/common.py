from datetime import date, datetime, time, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict


class PersistenceModel(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
        populate_by_name=True,
    )

    def to_mongo(self) -> dict[str, Any]:
        return self._to_mongo_value(self.model_dump(by_alias=True, exclude_none=True))

    @classmethod
    def from_mongo(cls, document: dict[str, Any]):
        return cls.model_validate(document)

    @classmethod
    def _to_mongo_value(cls, value: Any) -> Any:
        if isinstance(value, datetime):
            return value

        if isinstance(value, date):
            return datetime.combine(value, time.min, tzinfo=timezone.utc)

        if isinstance(value, dict):
            return {key: cls._to_mongo_value(item) for key, item in value.items()}

        if isinstance(value, list):
            return [cls._to_mongo_value(item) for item in value]

        if isinstance(value, tuple):
            return [cls._to_mongo_value(item) for item in value]

        return value


def mongo_datetime(value: datetime | None) -> datetime | None:
    return value
