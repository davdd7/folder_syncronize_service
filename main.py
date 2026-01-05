from services import SyncService


if __name__ == "__main__":
    sync_service = SyncService(".config.ini")
    sync_service.run()
