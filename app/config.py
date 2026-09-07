import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is required. Set it in .env")

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
ALGORITHM = "HS256"

# Telemetry
TELEMETRY_ENABLED = os.getenv("TELEMETRY_ENABLED", "true").strip().lower() == "true"
TELEMETRY_ENV = os.getenv("TELEMETRY_ENV", "development")
APP_VERSION = os.getenv("APP_VERSION", "0.1.0")

# Supabase (for production telemetry sink)
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
SUPABASE_TELEMETRY_TABLE = os.getenv("SUPABASE_TELEMETRY_TABLE", "telemetry_events")

# Anti-abuse
MAX_EVENT_BATCH_SIZE = int(os.getenv("MAX_EVENT_BATCH_SIZE", "100"))
MAX_CONTEXT_SIZE_BYTES = int(os.getenv("MAX_CONTEXT_SIZE_BYTES", "10240"))
