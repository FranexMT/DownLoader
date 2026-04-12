"""Tests para src/core/downloader.py — DownloadTask

Cubre:
- DownloadTask: inicializacion, atributos, y transiciones de estado
- pause(), resume(), stop() y sus efectos en status y eventos
"""

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


def _make_task(task_id=1, url="https://example.com/file.zip", tmp_path=None):
    """Crea un DownloadTask con load_config mockeado."""
    from src.core.downloader import DownloadTask
    dest = tmp_path if tmp_path else Path("/tmp")
    with patch("src.core.downloader.load_config", return_value={
        "default_threads": 4,
        "max_speed_kbps": 0,
    }):
        return DownloadTask(task_id=task_id, url=url, destination=dest)


# ---------------------------------------------------------------------------
# Inicializacion
# ---------------------------------------------------------------------------

class TestDownloadTaskInit:
    def test_initial_status_is_pending(self, tmp_path):
        task = _make_task(tmp_path=tmp_path)
        from src.core.downloader import DownloadTask
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
        """El evento de pausa debe estar activo (sin pausar) al crear la tarea."""
        task = _make_task(tmp_path=tmp_path)
        assert task._pause_event.is_set()

    def test_stop_event_not_set_by_default(self, tmp_path):
        task = _make_task(tmp_path=tmp_path)
        assert not task._stop_event.is_set()

    def test_status_constants_defined(self, tmp_path):
        from src.core.downloader import DownloadTask
        assert hasattr(DownloadTask, "STATUS_PENDING")
        assert hasattr(DownloadTask, "STATUS_DOWNLOADING")
        assert hasattr(DownloadTask, "STATUS_PAUSED")
        assert hasattr(DownloadTask, "STATUS_COMPLETED")
        assert hasattr(DownloadTask, "STATUS_FAILED")
        assert hasattr(DownloadTask, "STATUS_CANCELLED")


# ---------------------------------------------------------------------------
# pause() / resume()
# ---------------------------------------------------------------------------

class TestDownloadTaskPauseResume:
    def test_pause_changes_status_when_downloading(self, tmp_path):
        from src.core.downloader import DownloadTask
        task = _make_task(tmp_path=tmp_path)
        task.status = DownloadTask.STATUS_DOWNLOADING
        with patch("src.core.downloader.db", MagicMock()):
            task.pause()
        assert task.status == DownloadTask.STATUS_PAUSED

    def test_pause_clears_pause_event(self, tmp_path):
        from src.core.downloader import DownloadTask
        task = _make_task(tmp_path=tmp_path)
        task.status = DownloadTask.STATUS_DOWNLOADING
        with patch("src.core.downloader.db", MagicMock()):
            task.pause()
        assert not task._pause_event.is_set()

    def test_pause_does_nothing_when_not_downloading(self, tmp_path):
        from src.core.downloader import DownloadTask
        task = _make_task(tmp_path=tmp_path)
        task.status = DownloadTask.STATUS_PENDING
        with patch("src.core.downloader.db", MagicMock()):
            task.pause()
        assert task.status == DownloadTask.STATUS_PENDING

    def test_resume_changes_status_when_paused(self, tmp_path):
        from src.core.downloader import DownloadTask
        task = _make_task(tmp_path=tmp_path)
        task.status = DownloadTask.STATUS_PAUSED
        task._pause_event.clear()
        with patch("src.core.downloader.db", MagicMock()):
            task.resume()
        assert task.status == DownloadTask.STATUS_DOWNLOADING

    def test_resume_sets_pause_event(self, tmp_path):
        from src.core.downloader import DownloadTask
        task = _make_task(tmp_path=tmp_path)
        task.status = DownloadTask.STATUS_PAUSED
        task._pause_event.clear()
        with patch("src.core.downloader.db", MagicMock()):
            task.resume()
        assert task._pause_event.is_set()

    def test_resume_does_nothing_when_not_paused(self, tmp_path):
        from src.core.downloader import DownloadTask
        task = _make_task(tmp_path=tmp_path)
        task.status = DownloadTask.STATUS_COMPLETED
        with patch("src.core.downloader.db", MagicMock()):
            task.resume()
        assert task.status == DownloadTask.STATUS_COMPLETED

    def test_pause_then_resume_cycle(self, tmp_path):
        from src.core.downloader import DownloadTask
        task = _make_task(tmp_path=tmp_path)
        task.status = DownloadTask.STATUS_DOWNLOADING
        with patch("src.core.downloader.db", MagicMock()):
            task.pause()
            assert task.status == DownloadTask.STATUS_PAUSED
            task.resume()
            assert task.status == DownloadTask.STATUS_DOWNLOADING


# ---------------------------------------------------------------------------
# stop()
# ---------------------------------------------------------------------------

class TestDownloadTaskStop:
    def test_stop_sets_stop_event(self, tmp_path):
        task = _make_task(tmp_path=tmp_path)
        task.stop()
        assert task._stop_event.is_set()

    def test_stop_also_sets_pause_event(self, tmp_path):
        """stop() desbloquea cualquier hilo esperando en _pause_event."""
        task = _make_task(tmp_path=tmp_path)
        task._pause_event.clear()
        task.stop()
        assert task._pause_event.is_set()
