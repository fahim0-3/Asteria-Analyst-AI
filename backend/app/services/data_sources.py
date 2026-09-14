import hashlib
import re
from pathlib import Path

import pandas as pd
from fastapi import HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.analytics.profiling import profile_frame
from app.core.config import get_settings
from app.db.models import DataSource, DataSourceColumn, User


def safe_name(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]", "_", Path(name).name)
    if cleaned in {"", ".", ".."}:
        raise HTTPException(400, "Invalid filename")
    return cleaned


def read_frame(path: Path, **options: object) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path, **options)
    if suffix == ".xlsx":
        return pd.read_excel(path, **options)
    if suffix == ".parquet":
        return pd.read_parquet(path)
    raise HTTPException(415, "Unsupported file type")


def owned_source(db: Session, source_id: str, user: User) -> DataSource:
    source = db.scalar(select(DataSource).where(DataSource.id == source_id, DataSource.owner_id == user.id))
    if source is None:
        raise HTTPException(404, "Data source not found")
    return source


def ingest_upload(db: Session, user: User, upload: UploadFile) -> DataSource:
    settings = get_settings()
    filename = safe_name(upload.filename or "upload")
    suffix = Path(filename).suffix.lower()
    if suffix not in settings.allowed_extensions:
        raise HTTPException(415, f"Allowed file types: {', '.join(sorted(settings.allowed_extensions))}")
    content = upload.file.read(settings.max_upload_size_mb * 1024 * 1024 + 1)
    if len(content) > settings.max_upload_size_mb * 1024 * 1024:
        raise HTTPException(413, "Upload exceeds configured size limit")
    digest = hashlib.sha256(content).hexdigest()
    duplicate = db.scalar(select(DataSource).where(DataSource.owner_id == user.id, DataSource.file_hash == digest))
    if duplicate:
        raise HTTPException(409, f"This file is already available as '{duplicate.name}'")
    settings.data_upload_directory.mkdir(parents=True, exist_ok=True)
    source = DataSource(owner_id=user.id, name=Path(filename).stem, file_name=filename, file_hash=digest, status="profiling")
    db.add(source)
    db.flush()
    path = settings.data_upload_directory / f"{source.id}{suffix}"
    path.write_bytes(content)
    try:
        frame = read_frame(path)
        if frame.columns.duplicated().any():
            raise ValueError("Duplicate column names are not supported")
        profile = profile_frame(frame)
        source.storage_path = str(path.resolve())
        source.row_count = len(frame)
        source.column_count = len(frame.columns)
        source.profile = profile
        source.status = "ready"
        for item in profile["columns"]:
            db.add(DataSourceColumn(
                data_source_id=source.id, column_name=item["name"], inferred_type=item["inferred_type"],
                nullable=item["missing_count"] > 0, unique_count=item["unique_count"],
                missing_count=item["missing_count"], sample_values=item["sample_values"],
            ))
        db.commit()
        db.refresh(source)
        return source
    except Exception as exc:
        source.status = "failed"
        source.error_message = str(exc)[:500]
        db.commit()
        path.unlink(missing_ok=True)
        raise HTTPException(422, f"The file could not be parsed: {exc}") from exc


def delete_source(db: Session, source: DataSource) -> None:
    if source.storage_path:
        Path(source.storage_path).unlink(missing_ok=True)
    db.delete(source)
    db.commit()

