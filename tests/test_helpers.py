"""Tests for src/utils/helpers.py"""

import time
import re
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from src.utils.helpers import (
    format_bytes,
    format_timestamp,
    calculate_eta,
    format_speed,
    get_file_extension,
    get_file_icon,
    check_ffmpeg,
    open_file,
    send_notification,
)


# ---------------------------------------------------------------------------
# format_bytes
# ---------------------------------------------------------------------------

class TestFormatBytes:
    def test_format_bytes_zero(self):
        assert format_bytes(0) == "0 B"

    def test_format_bytes_negative(self):
        assert format_bytes(-1) == "0 B"

    def test_format_bytes_bytes(self):
        assert format_bytes(512) == "512 B"

    def test_format_bytes_exactly_1kb(self):
        result = format_bytes(1024)
        assert result == "1.00 KB"

    def test_format_bytes_kilobytes(self):
        # 2048 bytes == 2.00 KB
        assert format_bytes(2048) == "2.00 KB"

    def test_format_bytes_megabytes(self):
        # 1024 * 1024 == 1 MB
        result = format_bytes(1024 * 1024)
        assert result == "1.00 MB"

    def test_format_bytes_gigabytes(self):
        result = format_bytes(1024 ** 3)
        assert result == "1.00 GB"

    def test_format_bytes_large_value(self):
        # 1.5 GB
        result = format_bytes(int(1.5 * 1024 ** 3))
        assert "GB" in result
        assert "1.50" in result

    def test_format_bytes_one_byte(self):
        assert format_bytes(1) == "1 B"


# ---------------------------------------------------------------------------
# format_timestamp
# ---------------------------------------------------------------------------

class TestFormatTimestamp:
    def test_format_timestamp_returns_string(self):
        ts = time.time()
        result = format_timestamp(ts)
        assert isinstance(result, str)

    def test_format_timestamp_correct_format(self):
        # FIX: format uses %S (uppercase, seconds) not %s (unix timestamp)
        # Pattern: YYYY-MM-DD HH:MM:SS
        ts = time.time()
        result = format_timestamp(ts)
        pattern = r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$"
        assert re.match(pattern, result), f"Unexpected format: {result}"

    def test_format_timestamp_known_value(self):
        # Unix epoch (UTC) — use local-aware approach via datetime
        from datetime import datetime
        ts = 0.0
        result = format_timestamp(ts)
        expected = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
        assert result == expected

    def test_format_timestamp_recent(self):
        # Should not contain raw epoch integer (i.e., not the %s placeholder bug)
        ts = 1_700_000_000.0
        result = format_timestamp(ts)
        assert str(int(ts)) not in result


# ---------------------------------------------------------------------------
# calculate_eta
# ---------------------------------------------------------------------------

class TestCalculateEta:
    def test_calculate_eta_seconds(self):
        # 100 bytes remaining at 10 B/s -> 10 seconds
        result = calculate_eta(0, 100, 10.0)
        assert result == "10s"

    def test_calculate_eta_minutes(self):
        # 600 bytes remaining at 10 B/s -> 60 seconds -> "1:00"
        result = calculate_eta(0, 600, 10.0)
        assert result == "1:00"

    def test_calculate_eta_hours(self):
        # 7200 bytes remaining at 1 B/s -> 7200 seconds -> "2h 0m"
        result = calculate_eta(0, 7200, 1.0)
        assert result == "2h 0m"

    def test_calculate_eta_zero_speed_returns_placeholder(self):
        result = calculate_eta(0, 1000, 0)
        assert result == "--:--"

    def test_calculate_eta_negative_speed_returns_placeholder(self):
        result = calculate_eta(0, 1000, -5.0)
        assert result == "--:--"

    def test_calculate_eta_already_complete_returns_placeholder(self):
        # downloaded >= total means nothing left
        result = calculate_eta(1000, 1000, 100.0)
        assert result == "--:--"

    def test_calculate_eta_more_downloaded_than_total(self):
        result = calculate_eta(1500, 1000, 100.0)
        assert result == "--:--"

    def test_calculate_eta_partial_minutes(self):
        # 90 bytes remaining at 1 B/s -> 90 seconds -> "1:30"
        result = calculate_eta(0, 90, 1.0)
        assert result == "1:30"


# ---------------------------------------------------------------------------
# format_speed
# ---------------------------------------------------------------------------

class TestFormatSpeed:
    def test_format_speed_zero(self):
        assert format_speed(0) == "0 B/s"

    def test_format_speed_negative(self):
        assert format_speed(-100) == "0 B/s"

    def test_format_speed_bytes_per_second(self):
        result = format_speed(512)
        assert result == "512 B/s"

    def test_format_speed_kilobytes_per_second(self):
        result = format_speed(1024)
        assert "KB/s" in result

    def test_format_speed_megabytes_per_second(self):
        result = format_speed(1024 * 1024)
        assert "MB/s" in result

    def test_format_speed_ends_with_per_second(self):
        result = format_speed(2048)
        assert result.endswith("/s")


# ---------------------------------------------------------------------------
# get_file_extension
# ---------------------------------------------------------------------------

class TestGetFileExtension:
    def test_get_file_extension_standard(self):
        assert get_file_extension("archive.zip") == "zip"

    def test_get_file_extension_double_extension(self):
        # rsplit('.', 1)[1] takes only the last segment
        assert get_file_extension("file.tar.gz") == "gz"

    def test_get_file_extension_uppercase_lowercased(self):
        assert get_file_extension("IMAGE.JPG") == "jpg"

    def test_get_file_extension_no_extension(self):
        assert get_file_extension("Makefile") == ""

    def test_get_file_extension_hidden_file(self):
        # ".bashrc" has no extension after the leading dot under this logic
        assert get_file_extension(".bashrc") == "bashrc"

    def test_get_file_extension_dotfile_with_ext(self):
        assert get_file_extension(".config.yaml") == "yaml"


# ---------------------------------------------------------------------------
# get_file_icon
# ---------------------------------------------------------------------------

class TestGetFileIcon:
    @pytest.mark.parametrize("ext,expected", [
        ("zip",  "📦"),
        ("rar",  "📦"),
        ("7z",   "📦"),
        ("tar",  "📦"),
        ("gz",   "📦"),
        ("mp3",  "🎵"),
        ("wav",  "🎵"),
        ("flac", "🎵"),
        ("mp4",  "🎬"),
        ("avi",  "🎬"),
        ("mkv",  "🎬"),
        ("mov",  "🎬"),
        ("jpg",  "🖼️"),
        ("jpeg", "🖼️"),
        ("png",  "🖼️"),
        ("gif",  "🖼️"),
        ("svg",  "🖼️"),
        ("pdf",  "📕"),
        ("doc",  "📄"),
        ("docx", "📄"),
        ("txt",  "📝"),
        ("xls",  "📊"),
        ("xlsx", "📊"),
        ("exe",  "⚙️"),
        ("msi",  "⚙️"),
        ("apk",  "📱"),
        ("deb",  "📦"),
        ("rpm",  "📦"),
        ("iso",  "💿"),
    ])
    def test_get_file_icon_known_extensions(self, ext, expected):
        assert get_file_icon(ext) == expected

    def test_get_file_icon_unknown_extension_returns_default(self):
        assert get_file_icon("xyz") == "📁"

    def test_get_file_icon_empty_extension_returns_default(self):
        assert get_file_icon("") == "📁"

    def test_get_file_icon_uppercase_extension(self):
        # get_file_icon calls .lower() internally
        assert get_file_icon("ZIP") == "📦"
        assert get_file_icon("MP4") == "🎬"


# ---------------------------------------------------------------------------
# check_ffmpeg
# ---------------------------------------------------------------------------

class TestCheckFfmpeg:
    def test_check_ffmpeg_found(self):
        with patch("shutil.which", return_value="/usr/bin/ffmpeg"):
            result = check_ffmpeg()
        assert result is True

    def test_check_ffmpeg_not_found(self):
        with patch("shutil.which", return_value=None):
            result = check_ffmpeg()
        assert result is False


# ---------------------------------------------------------------------------
# open_file
# ---------------------------------------------------------------------------

class TestOpenFile:
    def test_open_file_nonexistent_returns_false(self, tmp_path):
        result = open_file(str(tmp_path / "no_such_file.txt"))
        assert result is False

    def test_open_file_linux_success(self, tmp_path):
        fpath = tmp_path / "test.txt"
        fpath.write_text("hello")
        with patch("sys.platform", "linux"), \
             patch("subprocess.Popen") as mock_popen:
            result = open_file(str(fpath))
        assert result is True
        mock_popen.assert_called_once_with(["xdg-open", str(fpath)])

    def test_open_file_darwin_success(self, tmp_path):
        fpath = tmp_path / "test.txt"
        fpath.write_text("hello")
        with patch("sys.platform", "darwin"), \
             patch("subprocess.Popen") as mock_popen:
            result = open_file(str(fpath))
        assert result is True
        mock_popen.assert_called_once_with(["open", str(fpath)])

    def test_open_file_exception_returns_false(self, tmp_path):
        fpath = tmp_path / "test.txt"
        fpath.write_text("hello")
        with patch("sys.platform", "linux"), \
             patch("subprocess.Popen", side_effect=OSError("popen failed")):
            result = open_file(str(fpath))
        assert result is False


# ---------------------------------------------------------------------------
# send_notification
# ---------------------------------------------------------------------------

class TestSendNotification:
    def test_send_notification_calls_plyer(self):
        mock_notif = MagicMock()
        with patch.dict("sys.modules", {"plyer": MagicMock(notification=mock_notif)}):
            # Should not raise
            send_notification("Title", "Message")

    def test_send_notification_handles_import_error_gracefully(self):
        # When plyer is unavailable the exception branch runs silently
        with patch.dict("sys.modules", {"plyer": None}):
            # Should not raise
            send_notification("Title", "Message")
