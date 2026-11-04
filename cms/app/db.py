from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

_is_sqlite = settings.database_url.startswith("sqlite")

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    # FastAPI runs sync endpoints in a threadpool; SQLite's same-thread check
    # would reject that.
    connect_args={"check_same_thread": False} if _is_sqlite else {},
)

if _is_sqlite:

    @event.listens_for(engine, "connect")
    def _sqlite_pragmas(dbapi_conn, _record):
        cur = dbapi_conn.cursor()
        # SQLite ignores ON DELETE CASCADE unless foreign keys are enabled.
        cur.execute("PRAGMA foreign_keys=ON")
        # WAL lets the API read while the admin writes, and is what Litestream
        # replicates. busy_timeout waits out a brief lock instead of erroring.
        cur.execute("PRAGMA journal_mode=WAL")
        cur.execute("PRAGMA busy_timeout=5000")
        cur.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
