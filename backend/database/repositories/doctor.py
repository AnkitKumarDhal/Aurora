from backend.models.doctor import DoctorDocument
from .base import BaseRepository


class DoctorRepository(BaseRepository[DoctorDocument]):
    collection_name = DoctorDocument.collection_name
    model = DoctorDocument

    async def get_doctor(self, doctor_id: str,) -> DoctorDocument | None:
        return await self.get_one({"doctor_id": doctor_id})

    async def get_department_doctors(self, department_id: str,) -> list[DoctorDocument]:
        cursor = self.collection.find({
            "department_ids": department_id,
        })

        return [
            self.model.from_mongo(document)
            async for document in cursor
        ]

    async def get_available_department_doctors(self, department_id: str,) -> list[DoctorDocument]:
        cursor = self.collection.find({
            "department_ids": department_id,
            "is_available": True,
        })

        return [
            self.model.from_mongo(document)
            async for document in cursor
        ]

    async def create_doctor(self, doctor: DoctorDocument,) -> DoctorDocument:
        return await self.create(doctor)

    async def update_doctor(self, doctor_id: str, updates: dict,) -> DoctorDocument | None:
        return await self.update_one({"doctor_id": doctor_id}, updates,)
