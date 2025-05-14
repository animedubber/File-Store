import os

class Config:
    # Bot configuration
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN")
    DEVELOPER_ID = int(os.environ.get("DEVELOPER_ID", "123456789"))
    
    # Data storage paths
    DATA_DIR = "data"
    FILES_DATA = os.path.join(DATA_DIR, "files.json")
    USERS_DATA = os.path.join(DATA_DIR, "users.json")
    
    # Backup settings
    SAVE_INTERVAL = 300  # Save data every 5 minutes
    
    # File settings
    MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB max file size
    
    # Bot features
    ENABLE_SHORTENER = False  # URL shortener feature currently disabled
    ENABLE_BATCH = False      # Batch feature currently disabled
