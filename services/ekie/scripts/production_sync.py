"""Built-in production background worker for continuous document synchronization.

This script runs in an infinite loop, polling the directory specified in your
EKIE_SYNC__TARGET_DIRECTORY environment variable, and automatically sends newly
created or modified documents to the EKIE API for ingestion.

Usage:
    # 1. Set the variables in your .env file
    # EKIE_SYNC__TARGET_DIRECTORY=/mnt/shared_drive
    # EKIE_SYNC__TENANT_ID=tenant-default
    # EKIE_SYNC__POLL_INTERVAL_SECONDS=300
    # EKIE_SYNC__API_BASE_URL=http://localhost:8001
    
    # 2. Run the worker
    python services/ekie/scripts/production_sync.py
"""

from __future__ import annotations

import datetime
import sys
import time
from pathlib import Path

import requests

# Resolve the service root absolutely so that config.settings can locate .env
# regardless of the process working directory at launch time.
_SERVICE_ROOT = Path(__file__).resolve().parents[1]
_SRC = _SERVICE_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from config.settings import get_settings  # noqa: E402
from domain.control_plane import ControlPlaneDatabase  # noqa: E402
from domain.sync import (  # noqa: E402
    LocalFileSystemConnector,
    RepositoryConnectorConfig,
    RepositorySynchronizer,
    SyncEventType,
    SyncPolicy,
    register_repository,
)


def run_worker() -> None:
    settings = get_settings()
    sync_settings = settings.sync
    
    target_dir = sync_settings.target_directory
    if not target_dir:
        print("ERROR: EKIE_SYNC__TARGET_DIRECTORY is not set in your .env file.")
        print("Please configure this variable to point to the directory you want to sync.")
        sys.exit(1)
        
    target_path = Path(target_dir)
    if not target_path.exists() or not target_path.is_dir():
        print(
            "ERROR: The configured target directory does not exist "
            f"or is not a directory: {target_dir}"
        )
        sys.exit(1)

    tenant_id = sync_settings.tenant_id
    poll_interval = sync_settings.poll_interval_seconds
    api_url = sync_settings.api_base_url.rstrip('/')

    print("==================================================")
    print(" EKIE Production Sync Worker Started")
    print("==================================================")
    print(f" Target Directory : {target_dir}")
    print(f" Tenant ID        : {tenant_id}")
    print(f" Poll Interval    : {poll_interval} seconds")
    print(f" API Base URL     : {api_url}")
    print("==================================================\n")

    # Connect to the Control Plane Database and ensure tables exist
    db = ControlPlaneDatabase(settings.control_plane)
    db.create_all()
    
    # Register the repository
    repository_id = register_repository(
        db, 
        tenant_id=tenant_id, 
        name=f"auto-sync-{target_path.name}", 
        source_type="local_fs", 
        uri=target_dir
    )
    
    # Configure the scanner
    connector = LocalFileSystemConnector(
        RepositoryConnectorConfig(
            repository_id=repository_id, 
            tenant_id=tenant_id,
            name=f"auto-sync-{target_path.name}", 
            connector_type="local_fs", 
            root_uri=target_dir
        )
    )
    
    synchronizer = RepositorySynchronizer(db, connector, SyncPolicy())

    while True:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{now}] Waking up to scan for changes...")
        
        try:
            result = synchronizer.synchronize(repository_id, tenant_id)
            print(f"[{now}] Scan complete. Found {len(result.events)} changes.")

            for event in result.events:
                if event.event_type is SyncEventType.DOCUMENT_DELETED and event.document_id:
                    try:
                        response = requests.delete(
                            f"{api_url}/v1/documents/{event.document_id}/vectors",
                            headers={"X-Tenant-ID": tenant_id},
                            timeout=60,
                        )
                        if response.status_code == 200:
                            print(
                                "     [DELETE] Vector cleanup completed for deleted document "
                                f"{event.document_id}"
                            )
                        else:
                            print(
                                "     [ERROR] Vector cleanup API failed for deleted document "
                                f"{event.document_id}: {response.text}"
                            )
                    except Exception as exc:
                        print(
                            "     [ERROR] Vector cleanup failed for deleted document "
                            f"{event.document_id}: {exc}"
                        )
            
            for event in result.events:
                if event.event_type.value in ["DocumentDiscovered", "DocumentModified"]:
                    document_id = event.document_id
                    file_path = target_path / event.source_path
                    
                    try:
                        raw_bytes = file_path.read_bytes()
                        print(f"  -> Triggering ingestion for: {event.source_path}")
                        
                        response = requests.post(
                            f"{api_url}/v1/documents/{document_id}/ingest",
                            headers={
                                "X-Tenant-ID": tenant_id, 
                                "Content-Type": "application/octet-stream"
                            },
                            data=raw_bytes,
                            timeout=300,
                        )
                        
                        if response.status_code == 200:
                            print("     [SUCCESS] Vectorized successfully!")
                        else:
                            print(f"     [ERROR] Failed: {response.text}")
                    except Exception as e:
                        print(f"     [ERROR] Could not process {event.source_path}: {e}")
                        
        except Exception as e:
            print(f"[{now}] [ERROR] Synchronization loop failed: {e}")
            
        print(f"[{now}] Sleeping for {poll_interval} seconds...\n")
        time.sleep(poll_interval)


if __name__ == "__main__":
    run_worker()
