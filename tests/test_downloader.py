import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path


class TestDownloadTask:
    def test_initial_status_is_pending(self):
        from src.core.downloader import DownloadTask
        with patch("src.core.downloader.load_config", return_value={"default_threads": 4, "max_speed_kbps": 0}):
            task = DownloadTask(1, "https://example.com/file.zip", Path("/tmp"))
            assert task.status == DownloadTask.STATUS_PENDING

    def test_stop_sets_stop_event(self):
        from src.core.downloader import DownloadTask
        with patch("src.core.downloader.load_config", return_value={"default_threads": 4, "max_speed_kbps": 0}):
            task = DownloadTask(1, "https://example.com/file.zip", Path("/tmp"))
            task.stop()
            assert task._stop_event.is_set()

    def test_pause_requires_downloading_status(self):
        from src.core.downloader import DownloadTask
        with patch("src.core.downloader.load_config", return_value={"default_threads": 4, "max_speed_kbps": 0}):
            with patch("src.core.downloader.db") as mock_db:
                task = DownloadTask(1, "https://example.com/file.zip", Path("/tmp"))
                task.status = DownloadTask.STATUS_DOWNLOADING
                task.pause()
                assert task.status == DownloadTask.STATUS_PAUSED

    def test_resume_requires_paused_status(self):
        from src.core.downloader import DownloadTask
        with patch("src.core.downloader.load_config", return_value={"default_threads": 4, "max_speed_kbps": 0}):
            with patch("src.core.downloader.db") as mock_db:
                task = DownloadTask(1, "https://example.com/file.zip", Path("/tmp"))
                task.status = DownloadTask.STATUS_PAUSED
                task.resume()
                assert task.status == DownloadTask.STATUS_DOWNLOADING

    def test_status_constants_defined(self):
        from src.core.downloader import DownloadTask
        assert hasattr(DownloadTask, "STATUS_PENDING")
        assert hasattr(DownloadTask, "STATUS_DOWNLOADING")
        assert hasattr(DownloadTask, "STATUS_PAUSED")
        assert hasattr(DownloadTask, "STATUS_COMPLETED")
        assert hasattr(DownloadTask, "STATUS_FAILED")
        assert hasattr(DownloadTask, "STATUS_CANCELLED")
