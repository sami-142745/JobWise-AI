import logging
import time

from pymongo import ASCENDING, MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from .config import settings

logger = logging.getLogger(__name__)

client = None
db = None


def _connect(database: str | None = None) -> tuple[MongoClient, object]:
    """Connect to MongoDB, retrying a few times when the server is warming up."""
    global client, db
    uri = settings.MONGO_URI
    if client is None:
        client = MongoClient(uri, serverSelectionTimeoutMS=3000)
    db_name = database or settings.DATABASE_NAME
    db = client[db_name]
    client.admin.command("ping")
    return client, db


def connect() -> None:
    """Establish the connection and create indexes."""
    global db
    last_error: Exception | None = None
    for attempt in range(5):
        try:
            _client, db = _connect()
            db.users.create_index([("email", ASCENDING)], unique=True)
            db.users.create_index([("username", ASCENDING)], unique=True)
            db.jobs.create_index([("title", ASCENDING)])
            db.jobs.create_index([("skills", ASCENDING)])
            db.resumes.create_index([("user_id", ASCENDING)])
            logger.info("Connected to MongoDB at %s (db=%s)", settings.MONGO_URI, settings.DATABASE_NAME)
            return
        except (ConnectionFailure, ServerSelectionTimeoutError) as exc:
            last_error = exc
            time.sleep(2)
    raise RuntimeError(f"Could not connect to MongoDB at {settings.MONGO_URI}: {last_error}")


def get_db():
    if db is None:
        connect()
    return db


def ping() -> bool:
    try:
        get_db().command("ping")
        return True
    except Exception:
        return False