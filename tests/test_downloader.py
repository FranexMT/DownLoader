"""Tests para src/core/downloader.py

Cubre:
- DownloadTask: inicialización y transiciones de estado (pause/resume/stop)
- Downloader.create_task: URLs válidas e inválidas
- Downloader.pause_task / resume_task / cancel_task
"""

import threading
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from src.core.downloader import DownloadTask, Downloader


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_task(task_id=1, url="https://example.com/file.zip", destination=None, tmp_path=None):
    """Crea un DownloadTask con valores predeterminados."""
    dest = destination or (tmp_path / "downloads" if tmp_path else Path("/tmp"))
    with patch("src.core.downloader.load_config", return_value={
        "default_threads": 4,
        "max_speed_kbps": 0,
    }):
        return DownloadTask(task_id=task_id, url=url, destination=dest)


# ---------------------------------------------------------------------------
# DownloadTask — inicialización
# ---------------------------------------------------------------------------

class TestDownloadTaskInit:
    def test_initial_status_is_pending(self, tmp_path):
        task = _make_task(tmp_path=tmp_path)
        assert task.status == DownloadTask.STATUS_PENDING

    def test_initial_progress_is_zero(self, tmp_path):
        task = _make_task(tmp_path=tmp_path)
        assert task.progress == 0.0

    def test_task_id_stored(self, tmp_path):
        task = _make_task(task_id=42, tmp_path=tmp_path)
        assert task.id == 42

    def test_url_stored(self, tmp_path):
        url = "https://example.com/data.tar.gz"
        task = _make_task(url=url, tmp_path=tmp_path)
        assert task.url == url

    def test_pause_event_set_by_default(self, tmp_path):
        """_pause_event debe estar establecido (no pausado) al crear la tarea."""
        task = _make_task(tmp_path=tmp_path)
        assert task._pause_event.is_set()

    def test_stop_event_not_set_by_default(self, tmp_path):
        task = _make_task(tmp_path=tmp_path)
        assert not task._stop_event.is_set()


# ---------------------------------------------------------------------------
# DownloadTask — pause / resume
# ---------------------------------------------------------------------------

class TestDownloadTaskPauseResume:
    def test_pause_changes_status_when_downloading(self, tmp_path):
        task = _make_task(tmp_path=tmp_path)
        task.status = DownloadTask.STATUS_DOWNLOADING

        mock_db = MagicMock()
        with patch("src.core.downloader.db", mock_db):
            task.pause()

        assert task.status == DownloadTask.STATUS_PAUSED

    def test_pause_clears_pause_event(self, tmp_path):
        task = _make_task(tmp_path=tmp_path)
        task.status = DownloadTask.STATUS_DOWNLOADING

        mock_db = MagicMock()
        with patch("src.core.downloader.db", mock_db):
            task.pause()

        assert not task._pause_event.is_set()

    def test_pause_does_nothing_when_not_downloading(self, tmp_path):
        task = _make_task(tmp_path=tmp_path)
        task.status = DownloadTask.STATUS_PENDING

        mock_db = MagicMock()
        with patch("src.core.downloader.db", mock_db):
            task.pause()

        assert task.status == DownloadTask.STATUS_PENDING

    def test_resume_changes_status_when_paused(self, tmp_path):
        task = _make_task(tmp_path=tmp_path)
        task.status = DownloadTask.STATUS_PAUSED
        task._pause_event.clear()

        mock_db = MagicMock()
        with patch("src.core.downloader.db", mock_db):
            task.resume()

        assert task.status == DownloadTask.STATUS_DOWNLOADING

    def test_resume_sets_pause_event(self, tmp_path):
        task = _make_task(tmp_path=tmp_path)
        task.status = DownloadTask.STATUS_PAUSED
        task._pause_event.clear()

        mock_db = MagicMock()
        with patch("src.core.downloader.db", mock_db):
            task.resume()

        assert task._pause_event.is_set()

    def test_resume_does_nothing_when_not_paused(self, tmp_path):
        task = _make_task(tmp_path=tmp_path)
        task.status = DownloadTask.STATUS_COMPLETED

        mock_db = MagicMock()
        with patch("src.core.downloader.db", mock_db):
            task.resume()

        assert task.status == DownloadTask.STATUS_COMPLETED

    def test_pause_then_resume_cycle(self, tmp_path):
        task = _make_task(tmp_path=tmp_path)
        task.status = DownloadTask.STATUS_DOWNLOADING

        mock_db = MagicMock()
        with patch("src.core.downloader.db", mock_db):
            task.pause()
            assert task.status == DownloadTask.STATUS_PAUSED
            task.resume()
            assert task.status == DownloadTask.STATUS_DOWNLOADING


# ---------------------------------------------------------------------------
# DownloadTask — stop
# ---------------------------------------------------------------------------

class TestDownloadTaskStop:
    def test_stop_sets_stop_event(self, tmp_path):
        task = _make_task(tmp_path=tmp_path)
        task.stop()
        assert task._stop_event.is_set()

    def test_stop_also_sets_pause_event(self, tmp_path):
        """stop() debe desbloquear cualquier hilo esperando en pause_event."""
        task = _make_task(tmp_path=tmp_path)
        task._pause_event.clear()
        task.stop()
        assert task._pause_event.is_set()


# ---------------------------------------------------------------------------
# Downloader.create_task
# ---------------------------------------------------------------------------

class TestDownloaderCreateTask:
    @pytest.fixture()
    def dl(self, tmp_path):
        """Instancia de Downloader con dependencias mockeadas."""
        with patch("src.core.downloader.load_config", return_value={
            "default_threads": 4,
            "default_download_path": str(tmp_path),
            "max_speed_kbps": 0,
            "timeout": 30,
        }), patch("src.core.downloader.ChunkManager"), \
           patch("src.core.downloader.threading.Thread"), \
           patch("src.core.downloader.db") as mock_db:
            mock_db.create_download.return_value = 1
            downloader = Downloader()
            downloader._mock_db = mock_db
            yield downloader

    def test_create_task_valid_url_returns_task(self, dl, tmp_path):
        with patch("src.core.downloader.db", dl._mock_db), \
             patch("src.core.downloader.is_social_media_url", return_value=False):
            task = dl.create_task("https://example.com/file.zip")
        assert task is not None
        assert isinstance(task, DownloadTask)

    def test_create_task_invalid_url_returns_none(self, dl):
        with patch("src.core.downloader.db", dl._mock_db):
            task = dl.create_task("not_a_valid_url")
        assert task is None

    def test_create_task_empty_url_returns_none(self, dl):
        with patch("src.core.downloader.db", dl._mock_db):
            task = dl.create_task("")
        assert task is None

    def test_create_task_ftp_url_returns_none(self, dl):
        with patch("src.core.downloader.db", dl._mock_db):
            task = dl.create_task("ftp://example.com/file.zip")
        assert task is None

    def test_create_task_stores_task_in_tasks_dict(self, dl, tmp_path):
        with patch("src.core.downloader.db", dl._mock_db), \
             patch("src.core.downloader.is_social_media_url", return_value=False):
            task = dl.create_task("https://example.com/file.zip")
        assert task.id in dl.tasks

    def test_create_task_uses_provided_destination(self, dl, tmp_path):
        custom_dest = str(tmp_path / "custom")
        with patch("src.core.downloader.db", dl._mock_db), \
             patch("src.core.downloader.is_social_media_url", return_value=False):
            task = dl.create_task(
                "https://example.com/file.zip",
                destination=custom_dest,
            )
        assert task is not None
        assert str(task.destination) == custom_dest


# ---------------------------------------------------------------------------
# Downloader.pause_task / resume_task / cancel_task
# ---------------------------------------------------------------------------

class TestDownloaderTaskControl:
    @pytest.fixture()
    def dl_with_task(self, tmp_path):
        """Downloader con una tarea DOWNLOADING precargada."""
        with patch("src.core.downloader.load_config", return_value={
            "default_threads": 4,
            "default_download_path": str(tmp_path),
            "max_speed_kbps": 0,
            "timeout": 30,
        }), patch("src.core.downloader.ChunkManager"), \
           patch("src.core.downloader.threading.Thread"), \
           patch("src.core.downloader.db") as mock_db:
            mock_db.create_download.return_value = 1
            dl = Downloader()

            with patch("src.core.downloader.load_config", return_value={
                "default_threads": 4,
                "max_speed_kbps": 0,
            }):
                task = DownloadTask(
                    task_id=1,
                    url="https://example.com/file.zip",
                    destination=tmp_path,
                )
            task.status = DownloadTask.STATUS_DOWNLOADING
            dl.tasks[1] = task
            dl._mock_db = mock_db
            yield dl, task

    def test_pause_task_existing_returns_true(self, dl_with_task):
        dl, task = dl_with_task
        with patch("src.core.downloader.db", dl._mock_db):
            result = dl.pause_task(1)
        assert result is True

    def test_pause_task_nonexistent_returns_false(self, dl_with_task):
        dl, _ = dl_with_task
        result = dl.pause_task(999)
        assert result is False

    def test_pause_task_changes_task_status(self, dl_with_task):
        dl, task = dl_with_task
        with patch("src.core.downloader.db", dl._mock_db):
            dl.pause_task(1)
        assert task.status == DownloadTask.STATUS_PAUSED

    def test_resume_task_existing_returns_true(self, dl_with_task):
        dl, task = dl_with_task
        task.status = DownloadTask.STATUS_PAUSED
        task._pause_event.clear()
        with patch("src.core.downloader.db", dl._mock_db), \
             patch("src.core.downloader.threading.Thread"):
            result = dl.resume_task(1)
        assert result is True

    def test_resume_task_nonexistent_returns_false(self, dl_with_task):
        dl, _ = dl_with_task
        result = dl.resume_task(999)
        assert result is False

    def test_cancel_task_existing_returns_true(self, dl_with_task):
        dl, task = dl_with_task
        with patch("src.core.downloader.db", dl._mock_db):
            result = dl.cancel_task(1)
        assert result is True

    def test_cancel_task_nonexistent_returns_false(self, dl_with_task):
        dl, _ = dl_with_task
        result = dl.cancel_task(999)
        assert result is False

    def test_cancel_task_sets_cancelled_status(self, dl_with_task):
        dl, task = dl_with_task
        with patch("src.core.downloader.db", dl._mock_db):
            dl.cancel_task(1)
        assert task.status == DownloadTask.STATUS_CANCELLED

    def test_remove_task_deletes_from_tasks_dict(self, dl_with_task):
        dl, _ = dl_with_task
        with patch("src.core.downloader.db", dl._mock_db):
            result = dl.remove_task(1)
        assert result is True
        assert 1 not in dl.tasks

    def test_remove_task_nonexistent_returns_false(self, dl_with_task):
        dl, _ = dl_with_task
        result = dl.remove_task(999)
        assert result is False
