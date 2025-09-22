from flask import session
from supabase import Client


def get_user_client(supabase: Client):
    """Return a supabase client authenticated as the logged-in user."""
    
    token = session.get("access_token")
    if token:
        return supabase
    # if "access_token" not in session:
    #     return None
    supabase.auth.set_session(session["access_token"], session["refresh_token"])
    return supabase
