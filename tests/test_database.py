"""Tests for src/core/database.py"""

import os
import time
import pytest

from src.core.database import Database


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def db(tmp_path):
    """Fresh in-memory (file) Database backed by a temp directory."""
    db_file = tmp_path / "test.db"
    return Database(db_path=str(db_file))


# ---------------------------------------------------------------------------
# create_download
# ---------------------------------------------------------------------------

class TestCreateDownload:
    def test_create_download_returns_integer_id(self, db):
        # Arrange / Act
        row_id = db.create_download(
            url="https://example.com/file.zip",
            filename="file.zip",
            destination="/tmp",
        )
        # Assert
        assert isinstance(row_id, int)
        assert row_id > 0

    def test_create_download_record_is_retrievable(self, db):
        row_id = db.create_download(
            url="https://example.com/archive.tar.gz",
            filename="archive.tar.gz",
            destination="/downloads",
        )
        record = db.get_download(row_id)
        assert record is not None
        assert record["url"] == "https://example.com/archive.tar.gz"
        assert record["filename"] == "archive.tar.gz"
        assert record["destination"] == "/downloads"

    def test_create_download_status_defaults_to_pending(self, db):
        row_id = db.create_download(
            url="https://example.com/doc.pdf",
            filename="doc.pdf",
            destination="/tmp",
        )
        record = db.get_download(row_id)
        assert record["status"] == "PENDING"

    def test_create_download_filename_extracted_from_url_when_pending(self, db):
        # FIX: when filename == "pending", it should be extracted from the URL
        row_id = db.create_download(
            url="https://example.com/path/auto_named.zip",
            filename="pending",
            destination="/tmp",
        )
        record = db.get_download(row_id)
        assert record["filename"] == "auto_named.zip"

    def test_create_download_with_title_and_thumbnail(self, db):
        row_id = db.create_download(
            url="https://example.com/video.mp4",
            filename="video.mp4",
            destination="/videos",
            title="My Video",
            thumbnail="https://example.com/thumb.jpg",
        )
        record = db.get_download(row_id)
        assert record["title"] == "My Video"
        assert record["thumbnail"] == "https://example.com/thumb.jpg"

    def test_create_multiple_downloads_have_unique_ids(self, db):
        ids = [
            db.create_download(
                url=f"https://example.com/file{i}.zip",
                filename=f"file{i}.zip",
                destination="/tmp",
            )
            for i in range(5)
        ]
        assert len(set(ids)) == 5


# ---------------------------------------------------------------------------
# update_download
# ---------------------------------------------------------------------------

class TestUpdateDownload:
    def test_update_download_status(self, db):
        row_id = db.create_download(
            url="https://example.com/f.zip",
            filename="f.zip",
            destination="/tmp",
        )
        db.update_download(row_id, status="COMPLETED")
        record = db.get_download(row_id)
        assert record["status"] == "COMPLETED"

    def test_update_download_multiple_fields(self, db):
        row_id = db.create_download(
            url="https://example.com/f.zip",
            filename="f.zip",
            destination="/tmp",
        )
        db.update_download(row_id, total_size=1024, downloaded_size=512, speed=256.0)
        record = db.get_download(row_id)
        assert record["total_size"] == 1024
        assert record["downloaded_size"] == 512
        assert record["speed"] == 256.0

    def test_update_download_sets_updated_at(self, db):
        # FIX: updated_at is now set to datetime.utcnow().isoformat()
        row_id = db.create_download(
            url="https://example.com/file.zip",
            filename="file.zip",
            destination="/tmp",
        )
        db.update_download(row_id, status="DOWNLOADING")
        record = db.get_download(row_id)
        # updated_at should be a non-empty ISO string
        updated_at = record.get("updated_at")
        assert updated_at is not None
        assert isinstance(updated_at, str)
        assert len(updated_at) > 0

    def test_update_download_ignores_unknown_fields(self, db):
        row_id = db.create_download(
            url="https://example.com/file.zip",
            filename="file.zip",
            destination="/tmp",
        )
        # Should not raise even if unknown fields are passed
        db.update_download(row_id, nonexistent_field="value", status="PAUSED")
        record = db.get_download(row_id)
        assert record["status"] == "PAUSED"

    def test_update_download_with_no_valid_fields_does_nothing(self, db):
        row_id = db.create_download(
            url="https://example.com/file.zip",
            filename="file.zip",
            destination="/tmp",
        )
        # All fields are invalid — should silently return
        db.update_download(row_id, invalid_field="x")
        record = db.get_download(row_id)
        assert record["status"] == "PENDING"

    def test_update_download_error_message(self, db):
        row_id = db.create_download(
            url="https://example.com/bad.zip",
            filename="bad.zip",
            destination="/tmp",
        )
        db.update_download(row_id, status="FAILED", error_message="Connection refused")
        record = db.get_download(row_id)
        assert record["error_message"] == "Connection refused"


# ---------------------------------------------------------------------------
# get_statistics
# ---------------------------------------------------------------------------

class TestGetStatistics:
    def test_get_statistics_empty_db(self, db):
        stats = db.get_statistics()
        assert stats["total"] == 0
        assert stats["completed"] == 0
        assert stats["failed"] == 0
        assert stats["total_bytes"] == 0

    def test_get_statistics_counts_correctly(self, db):
        # Arrange: 2 completed, 1 failed, 1 pending
        for i in range(2):
            rid = db.create_download(
                url=f"https://example.com/ok{i}.zip",
                filename=f"ok{i}.zip",
                destination="/tmp",
            )
            db.update_download(rid, status="COMPLETED", total_size=1024)

        failed_id = db.create_download(
            url="https://example.com/bad.zip",
            filename="bad.zip",
            destination="/tmp",
        )
        db.update_download(failed_id, status="FAILED")

        db.create_download(
            url="https://example.com/pending.zip",
            filename="pending.zip",
            destination="/tmp",
        )

        # Act
        stats = db.get_statistics()

        # Assert
        assert stats["total"] == 4
        assert stats["completed"] == 2
        assert stats["failed"] == 1

    def test_get_statistics_total_bytes(self, db):
        for size in [500, 1500]:
            rid = db.create_download(
                url=f"https://example.com/f{size}.zip",
                filename=f"f{size}.zip",
                destination="/tmp",
            )
            db.update_download(rid, total_size=size)

        stats = db.get_statistics()
        assert stats["total_bytes"] == 2000


# ---------------------------------------------------------------------------
# clear_history
# ---------------------------------------------------------------------------

class TestClearHistory:
    def _seed(self, db, count=3, status="PENDING"):
        ids = []
        for i in range(count):
            rid = db.create_download(
                url=f"https://example.com/f{i}.zip",
                filename=f"f{i}.zip",
                destination="/tmp",
            )
            db.update_download(rid, status=status)
            ids.append(rid)
        return ids

    def test_clear_history_all(self, db):
        self._seed(db, count=3)
        deleted = db.clear_history()
        assert deleted == 3
        assert db.get_statistics()["total"] == 0

    def test_clear_history_by_status_completed(self, db):
        self._seed(db, count=2, status="COMPLETED")
        self._seed(db, count=1, status="FAILED")

        deleted = db.clear_history(status="COMPLETED")
        assert deleted == 2

        remaining = db.get_all_downloads()
        assert len(remaining) == 1
        assert remaining[0]["status"] == "FAILED"

    def test_clear_history_by_status_no_match(self, db):
        self._seed(db, count=2, status="PENDING")
        deleted = db.clear_history(status="COMPLETED")
        assert deleted == 0
        assert db.get_statistics()["total"] == 2

    def test_clear_history_empty_db_returns_zero(self, db):
        assert db.clear_history() == 0


# ---------------------------------------------------------------------------
# delete_download
# ---------------------------------------------------------------------------

class TestDeleteDownload:
    def test_delete_download_existing_record(self, db):
        row_id = db.create_download(
            url="https://example.com/todelete.zip",
            filename="todelete.zip",
            destination="/tmp",
        )
        result = db.delete_download(row_id)
        assert result is True
        assert db.get_download(row_id) is None

    def test_delete_download_nonexistent_id_returns_false(self, db):
        result = db.delete_download(999_999)
        assert result is False

    def test_delete_download_decrements_total(self, db):
        r1 = db.create_download(
            url="https://example.com/a.zip",
            filename="a.zip",
            destination="/tmp",
        )
        db.create_download(
            url="https://example.com/b.zip",
            filename="b.zip",
            destination="/tmp",
        )
        db.delete_download(r1)
        assert db.get_statistics()["total"] == 1

    def test_delete_download_does_not_affect_other_records(self, db):
        r1 = db.create_download(
            url="https://example.com/keep.zip",
            filename="keep.zip",
            destination="/tmp",
        )
        r2 = db.create_download(
            url="https://example.com/remove.zip",
            filename="remove.zip",
            destination="/tmp",
        )
        db.delete_download(r2)
        assert db.get_download(r1) is not None


# ---------------------------------------------------------------------------
# get_all_downloads / get_active_downloads / get_completed_downloads
# ---------------------------------------------------------------------------

class TestQueryMethods:
    def _create(self, db, url, filename, status):
        rid = db.create_download(url=url, filename=filename, destination="/tmp")
        db.update_download(rid, status=status)
        return rid

    def test_get_all_downloads_no_filter_returns_all(self, db):
        self._create(db, "https://example.com/a.zip", "a.zip", "COMPLETED")
        self._create(db, "https://example.com/b.zip", "b.zip", "FAILED")
        rows = db.get_all_downloads()
        assert len(rows) == 2

    def test_get_all_downloads_with_status_filter(self, db):
        self._create(db, "https://example.com/a.zip", "a.zip", "COMPLETED")
        self._create(db, "https://example.com/b.zip", "b.zip", "FAILED")
        rows = db.get_all_downloads(status="COMPLETED")
        assert len(rows) == 1
        assert rows[0]["status"] == "COMPLETED"

    def test_get_active_downloads_returns_pending_downloading_paused(self, db):
        self._create(db, "https://example.com/p.zip", "p.zip", "PENDING")
        self._create(db, "https://example.com/d.zip", "d.zip", "DOWNLOADING")
        self._create(db, "https://example.com/pa.zip", "pa.zip", "PAUSED")
        self._create(db, "https://example.com/c.zip", "c.zip", "COMPLETED")

        rows = db.get_active_downloads()
        statuses = {r["status"] for r in rows}
        assert statuses == {"PENDING", "DOWNLOADING", "PAUSED"}
        assert len(rows) == 3

    def test_get_completed_downloads(self, db):
        self._create(db, "https://example.com/c1.zip", "c1.zip", "COMPLETED")
        self._create(db, "https://example.com/c2.zip", "c2.zip", "COMPLETED")
        self._create(db, "https://example.com/f.zip", "f.zip", "FAILED")

        rows = db.get_completed_downloads()
        assert len(rows) == 2
        assert all(r["status"] == "COMPLETED" for r in rows)

    def test_get_all_downloads_empty_db(self, db):
        assert db.get_all_downloads() == []

    def test_get_active_downloads_empty_db(self, db):
        assert db.get_active_downloads() == []


# ---------------------------------------------------------------------------
# Migration: column addition is idempotent
# ---------------------------------------------------------------------------

class TestMigration:
    def test_reinitialise_existing_db_does_not_drop_data(self, tmp_path):
        # Create DB, insert a row, then construct a second Database instance
        # pointing to the same file — migration must not fail or lose data.
        db_file = tmp_path / "migrate.db"
        db1 = Database(db_path=str(db_file))
        rid = db1.create_download(
            url="https://example.com/file.zip",
            filename="file.zip",
            destination="/tmp",
        )

        db2 = Database(db_path=str(db_file))
        record = db2.get_download(rid)
        assert record is not None
        assert record["filename"] == "file.zip"
