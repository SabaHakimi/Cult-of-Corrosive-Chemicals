import os
import dotenv
from sqlalchemy import create_engine

def database_connection_url():
    dotenv.load_dotenv()

    return os.environ.get("POSTGRES_URI", "postgresql://postgres:$Sekiro54807@db.ygsljlcupmsikfaduldh.supabase.co:5432/postgres")

engine = create_engine(database_connection_url(), pool_pre_ping=True)
