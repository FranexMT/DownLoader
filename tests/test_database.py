import pytest
import os
import tempfile
from src.core.database import Database


@pytest.fixture
def db(tmp_path):
    """Base de datos temporal para cada test."""
    db_file = tmp_path / "test.db"
    database = Database(db_path=str(db_file))
    yield database


class TestDatabaseCreate:
    def test_create_download_returns_id(self, db):
        id_ = db.create_download("https://example.com/file.zip", "pending", "/tmp")
        assert isinstance(id_, int)
        assert id_ > 0

    def test_create_stores_url(self, db):
        url = "https://example.com/archivo.zip"
        id_ = db.create_download(url, "pending", "/tmp")
        record = db.get_download(id_)
        assert record["url"] == url


class TestDatabaseUpdate:
    def test_update_status(self, db):
        id_ = db.create_download("https://example.com/f.zip", "pending", "/tmp")
        db.update_download(id_, status="COMPLETED")
        record = db.get_download(id_)
        assert record["status"] == "COMPLETED"

    def test_update_size(self, db):
        id_ = db.create_download("https://example.com/f.zip", "pending", "/tmp")
        db.update_download(id_, total_size=1024, downloaded_size=512)
        record = db.get_download(id_)
        assert record["total_size"] == 1024
        assert record["downloaded_size"] == 512


class TestDatabaseQuery:
    def test_get_all_downloads(self, db):
        db.create_download("https://example.com/a.zip", "pending", "/tmp")
        db.create_download("https://example.com/b.zip", "pending", "/tmp")
        all_ = db.get_all_downloads()
        assert len(all_) >= 2

    def test_get_nonexistent_returns_none(self, db):
        assert db.get_download(99999) is None

    def test_delete_download(self, db):
        id_ = db.create_download("https://example.com/f.zip", "pending", "/tmp")
        result = db.delete_download(id_)
        assert result is True
        assert db.get_download(id_) is None

    def test_statistics(self, db):
        id_ = db.create_download("https://example.com/f.zip", "pending", "/tmp")
        db.update_download(id_, status="COMPLETED")
        stats = db.get_statistics()
        assert "total" in stats
        assert "completed" in stats
        assert stats["completed"] >= 1
