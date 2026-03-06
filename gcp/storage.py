"""
GCP Cloud Storage — File upload/download for pipeline state.

Replaces local filesystem reads/writes with GCS bucket operations.
Falls back to local filesystem when GCS is not configured (local dev).

Usage:
    from gcp.storage import gcs_read_json, gcs_write_json

    # Read from GCS (or fallback to local)
    data = gcs_read_json("dossier/persistence/data/signal_history.json")

    # Write to GCS (and local)
    gcs_write_json("dossier/persistence/data/signal_history.json", data)
"""

import json
import os
from pathlib import Path
from functools import lru_cache

# Default bucket name — overridden by env var
DEFAULT_BUCKET = "mphinance-pipeline-data"


@lru_cache(maxsize=1)
def _get_bucket():
    """Get GCS bucket client, or None if not configured."""
    bucket_name = os.environ.get("GCS_BUCKET", DEFAULT_BUCKET)

    try:
        from google.cloud import storage
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        # Quick existence check
        if bucket.exists():
            return bucket
        else:
            print(f"[GCS] Bucket '{bucket_name}' does not exist, using local filesystem")
            return None
    except Exception as e:
        print(f"[GCS] Not available ({e}), using local filesystem")
        return None


def gcs_read_json(path: str, fallback_local: bool = True) -> dict | list | None:
    """
    Read a JSON file from GCS bucket.

    Args:
        path: Relative path within the bucket (e.g., "data/signal_history.json")
        fallback_local: If True, fall back to local filesystem when GCS unavailable

    Returns:
        Parsed JSON data, or None if file not found
    """
    bucket = _get_bucket()

    if bucket:
        try:
            blob = bucket.blob(path)
            if blob.exists():
                content = blob.download_as_text()
                return json.loads(content)
            else:
                print(f"[GCS] File not found: gs://{bucket.name}/{path}")
        except Exception as e:
            print(f"[GCS] Read error for {path}: {e}")

    # Fallback to local filesystem
    if fallback_local:
        local_path = Path(path)
        if local_path.exists():
            try:
                with open(local_path) as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"[LOCAL] Read error for {path}: {e}")

    return None


def gcs_write_json(path: str, data: dict | list, also_local: bool = True) -> bool:
    """
    Write JSON data to GCS bucket.

    Args:
        path: Relative path within the bucket
        data: JSON-serializable data
        also_local: If True, also write to local filesystem (for backup/debugging)

    Returns:
        True if write succeeded (to either GCS or local)
    """
    content = json.dumps(data, indent=2)
    success = False

    # Write to GCS
    bucket = _get_bucket()
    if bucket:
        try:
            blob = bucket.blob(path)
            blob.upload_from_string(content, content_type="application/json")
            print(f"[GCS] Written: gs://{bucket.name}/{path}")
            success = True
        except Exception as e:
            print(f"[GCS] Write error for {path}: {e}")

    # Also write locally (or as fallback)
    if also_local or not success:
        local_path = Path(path)
        local_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(local_path, "w") as f:
                f.write(content)
            success = True
        except IOError as e:
            print(f"[LOCAL] Write error for {path}: {e}")

    return success


def gcs_upload_file(local_path: str, gcs_path: str = None) -> bool:
    """
    Upload a local file to GCS.

    Args:
        local_path: Path to local file
        gcs_path: Destination path in bucket (defaults to local_path)
    """
    bucket = _get_bucket()
    if not bucket:
        return False

    gcs_path = gcs_path or local_path

    try:
        blob = bucket.blob(gcs_path)
        blob.upload_from_filename(local_path)
        print(f"[GCS] Uploaded: {local_path} → gs://{bucket.name}/{gcs_path}")
        return True
    except Exception as e:
        print(f"[GCS] Upload error: {e}")
        return False


def gcs_download_file(gcs_path: str, local_path: str = None) -> bool:
    """
    Download a file from GCS to local filesystem.

    Args:
        gcs_path: Source path in bucket
        local_path: Destination local path (defaults to gcs_path)
    """
    bucket = _get_bucket()
    if not bucket:
        return False

    local_path = local_path or gcs_path

    try:
        blob = bucket.blob(gcs_path)
        if not blob.exists():
            print(f"[GCS] File not found: gs://{bucket.name}/{gcs_path}")
            return False

        Path(local_path).parent.mkdir(parents=True, exist_ok=True)
        blob.download_to_filename(local_path)
        print(f"[GCS] Downloaded: gs://{bucket.name}/{gcs_path} → {local_path}")
        return True
    except Exception as e:
        print(f"[GCS] Download error: {e}")
        return False


def gcs_list_files(prefix: str = "") -> list[str]:
    """List files in the GCS bucket with optional prefix filter."""
    bucket = _get_bucket()
    if not bucket:
        return []

    try:
        blobs = bucket.list_blobs(prefix=prefix)
        return [blob.name for blob in blobs]
    except Exception as e:
        print(f"[GCS] List error: {e}")
        return []
