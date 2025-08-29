import os
from supabase import create_client, Client

# Load environment variables from .env
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY environment variables")

# Create Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def insert_signal(signal_data: dict):
    """
    Insert a new signal into the signals table.
    signal_data should include:
      - scanner_type
      - symbol
      - timeframe
      - signal_codes (list of strings)
      - signal_id
      - candle_timestamp
      - hadena_timestamp (optional)
      - entry_price (optional)
      - status (optional)
      - metadata (optional JSON)
    """
    response = supabase.table("signals").insert(signal_data).execute()
    return response

def update_scanner_status(scanner_id: str, status: str, error_message: str = None):
    """
    Update scanner_configs with last run status and timestamp.
    """
    from datetime import datetime, timezone
    update_data = {
        "last_run_timestamp": datetime.now(timezone.utc).isoformat(),
        "last_run_status": status,
    }
    if error_message:
        update_data["last_error_message"] = error_message

    response = supabase.table("scanner_configs").update(update_data).eq("scanner_id", scanner_id).execute()
    return response
