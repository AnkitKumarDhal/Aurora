from .common import TimestampedModel


class Doctor(TimestampedModel):
    doctor_id: str
    display_name: str

    department_ids: list[str] = []
    available: bool = True
