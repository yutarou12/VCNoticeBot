import os
from typing import List
import dotenv

dotenv.load_dotenv()

DISCORD_BOT_TOKEN: str = os.environ.get("DISCORD_BOT_TOKEN", "")
# DATABASE_URL: str = os.environ.get("DATABASE_URL", "")
# OWNERS: List[int] = list(map(int, os.environ.get("OWNERS", "").split(",")))

# TRACEBACK_CHANNEL_ID: int = int(os.environ.get("TRACEBACK_CHANNEL_ID", ""))
# ERROR_CHANNEL_ID: int = int(os.environ.get("ERROR_CHANNEL_ID", ""))

# DEBUG: bool = bool(os.environ.get("DEBUG", ""))
