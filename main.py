import os
from pathlib import Path

from services import SyncService

home = Path.home()
folder = home / "Desktop" / "SyncFolder"


if __name__ == "__main__":

    sync_service = SyncService(".config.ini")

    sync_service.run()
