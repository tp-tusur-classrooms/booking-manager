from src.domain.base.base_file_repository import BaseFileRepository
from src.domain.base.base_repository import BaseRepository
from src.domain.base.joiner import WithSchema
from src.domain.common.models import File
import src.domain.file.schemas as file_metadata_schemes


class FileMetadataRepository(
    BaseRepository[
        File,
        file_metadata_schemes.CreateFileMetadata,
        file_metadata_schemes.UpdateFileMetadata,
        file_metadata_schemes.FilterFileMetadata,
        WithSchema,
    ]
): ...


class FileRepository(BaseFileRepository): ...
