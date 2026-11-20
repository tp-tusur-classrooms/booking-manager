import asyncio
import io
import warnings

from fastapi import UploadFile
from PIL import Image, ImageOps, UnidentifiedImageError

from src.low.exceptions import FieldError, UserException

MAX_PHOTO_BYTES = 10 * 1024 * 1024


def photo_error(message: str, status: int, code: str) -> UserException:
    return UserException(
        message,
        status_code=status,
        code=code,
        errors=[FieldError(field="file", message=message)],
    )


def normalize_photo(content: bytes) -> tuple[bytes, str]:
    """Проверить декодирование и сохранить изображение без посторонних данных."""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(content)) as image:
                if image.format not in {"JPEG", "PNG"}:
                    raise photo_error(
                        "Загрузите изображение JPG или PNG",
                        415,
                        "unsupported_media_type",
                    )
                image.verify()
            with Image.open(io.BytesIO(content)) as image:
                image.load()
                result = ImageOps.exif_transpose(image)
                result.thumbnail((1920, 1920), Image.Resampling.LANCZOS)
                output = io.BytesIO()
                if image.format == "JPEG":
                    result.convert("RGB").save(output, format="JPEG", quality=90)
                    return output.getvalue(), ".jpg"
                result.save(output, format="PNG")
                return output.getvalue(), ".png"
    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
        SyntaxError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ) as exc:
        raise photo_error(
            "Загрузите изображение JPG или PNG", 415, "unsupported_media_type"
        ) from exc


async def prepare_photo(file: UploadFile) -> tuple[bytes, str]:
    # Не доверяем ни Content-Type, ни имени, ни размеру из заголовков клиента.
    content = await file.read(MAX_PHOTO_BYTES + 1)
    if len(content) > MAX_PHOTO_BYTES:
        raise photo_error("Файл должен быть не больше 10 МБ", 413, "file_too_large")
    return await asyncio.to_thread(normalize_photo, content)
