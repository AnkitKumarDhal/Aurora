from .common import TimestampedModel


class Department(TimestampedModel):
    department_id: str
    name: str
    active: bool = True
