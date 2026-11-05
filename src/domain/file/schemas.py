from datetime import datetime
import uuid

from pydantic import BaseModel


class FileMetadata(BaseModel):
    id: uuid.UUID
    created_at: datetime
    sub_folder: str
    original_filename: str
    stored_filename: str
    size: int
    user_id: uuid.UUID


class CreateFileMetadata(BaseModel):
    user_id: uuid.UUID
    sub_folder: str
    original_filename: str
    stored_filename: str
    size: int


class UpdateFileMetadata(BaseModel): ...


class FilterFileMetadata(BaseModel):
    id: list[uuid.UUID] | None = None
    user_id: list[uuid.UUID] | None = None
