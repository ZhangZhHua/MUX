"""Safe attachment storage primitives shared by experiment and event routes."""
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

MAX_UPLOAD_BYTES = 50 * 1024 * 1024
UPLOAD_ROOT = (Path(__file__).resolve().parents[1] / "uploads").resolve()

# The application only accepts formats it can identify from their content, not
# an extension or browser supplied Content-Type header.
MAGIC_TYPES = (
    (b"%PDF-", "pdf", "application/pdf"),
    (b"\x89PNG\r\n\x1a\n", "png", "image/png"),
    (b"\xff\xd8\xff", "jpg", "image/jpeg"),
    (b"GIF87a", "gif", "image/gif"),
    (b"GIF89a", "gif", "image/gif"),
    (b"BM", "bmp", "image/bmp"),
    (b"RIFF", "webp", "image/webp"),
    (b"PK\x03\x04", "zip", "application/zip"),
)


def _detect_type(content: bytes):
    for signature, extension, media_type in MAGIC_TYPES:
        if content.startswith(signature):
            if extension == "webp" and content[8:12] != b"WEBP":
                continue
            return extension, media_type
    return None


async def save_verified_upload(file: UploadFile) -> tuple[str, str, str, int, str]:
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Attachment is empty.")
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Attachment size exceeds the maximum limit of 50MB.")

    detected = _detect_type(content)
    if not detected:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Unsupported or unrecognized attachment content.")
    extension, media_type = detected
    # ZIP is accepted only for Office documents; generic archives are not an
    # attachment format supported by this application.
    original_name = Path(file.filename or "attachment").name
    if extension == "zip" and original_name.lower().split(".")[-1] not in {"docx", "xlsx", "pptx"}:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Only Office Open XML ZIP attachments are accepted.")
    if extension == "zip":
        extension = original_name.rsplit(".", 1)[-1].lower()

    UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
    storage_name = f"{uuid4().hex}.{extension}"
    path = (UPLOAD_ROOT / storage_name).resolve()
    if UPLOAD_ROOT not in path.parents:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid attachment path.")
    path.write_bytes(content)
    return storage_name, original_name, media_type, len(content), sha256(content).hexdigest()


def resolve_attachment_path(storage_name: str) -> Path:
    path = (UPLOAD_ROOT / storage_name).resolve()
    if UPLOAD_ROOT not in path.parents:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid attachment path.")
    if not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found.")
    return path
