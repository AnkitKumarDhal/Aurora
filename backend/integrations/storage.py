from pathlib import Path
from uuid import uuid4

import aiofiles
from fastapi import UploadFile


class LocalStorage:
    def __init__(self, root: str = "storage") -> None:
        self.root = Path(root)

    async def save(self, session_id: str, upload: UploadFile) -> str:
        session_directory = self.root / session_id
        session_directory.mkdir(parents=True, exist_ok=True)

        filename = Path(upload.filename or "document").name
        stored_name = f"{uuid4().hex}_{filename}"
        path = session_directory / stored_name

        async with aiofiles.open(path, "wb") as file:
            while chunk := await upload.read(1024 * 1024):
                await file.write(chunk)

        await upload.close()

        return str(path)

    async def delete(self, storage_reference: str) -> None:
        path = Path(storage_reference)

        if path.exists():
            path.unlink()
