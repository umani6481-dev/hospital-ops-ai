import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["DATABASE_URL"] = "sqlite:///./test_hospital_ops.db"

import pytest
from fastapi.testclient import TestClient

from app.database.session import Base, engine
from app.main import app


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("test_hospital_ops.db"):
        os.remove("test_hospital_ops.db")


@pytest.fixture
def client():
    return TestClient(app)
