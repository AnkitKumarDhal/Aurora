from backend.models.department import DepartmentDocument
from .base import BaseRepository


class DepartmentRepository(BaseRepository[DepartmentDocument]):
    collection_name = DepartmentDocument.collection_name
    model = DepartmentDocument

    async def get_department(self, department_id: str,) -> DepartmentDocument | None:
        return await self.get_one({"department_id": department_id})

    async def get_active_departments(self,) -> list[DepartmentDocument]:
        cursor = self.collection.find({
            "is_active": True,
        })

        return [
            self.model.from_mongo(document)
            async for document in cursor
        ]

    async def create_department(self, department: DepartmentDocument,) -> DepartmentDocument:
        return await self.create(department)

    async def update_department(self, department_id: str, updates: dict,) -> DepartmentDocument | None:
        return await self.update_one({"department_id": department_id}, updates,)
