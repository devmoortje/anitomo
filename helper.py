from dotenv import load_dotenv
from flask import session
from supabase import create_client, Client
import os


load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")
if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise RuntimeError("SUPABASE_URL or SUPABASE_ANON_KEY is not set")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

def get_user_client():
    """Return a supabase client authenticated as the logged-in user."""
    
    if "access_token" not in session:
        return None
    supabase.auth.set_session(session["access_token"], None)
    return supabase
