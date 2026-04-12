import pytest
from src.utils.helpers import (
    format_bytes,
    calculate_eta,
    format_speed,
    get_file_extension,
    get_file_icon,
)


class TestFormatBytes:
    def test_zero(self):
        assert format_bytes(0) == "0 B"

    def test_negative(self):
        assert format_bytes(-1) == "0 B"

    def test_bytes(self):
        assert format_bytes(500) == "500 B"

    def test_kilobytes(self):
        result = format_bytes(1024)
        assert "KB" in result

    def test_megabytes(self):
        result = format_bytes(1024 * 1024)
        assert "MB" in result

    def test_gigabytes(self):
        result = format_bytes(1024 * 1024 * 1024)
        assert "GB" in result


class TestCalculateEta:
    def test_zero_speed_returns_placeholder(self):
        assert calculate_eta(0, 1000, 0) == "--:--"

    def test_completed_returns_placeholder(self):
        assert calculate_eta(1000, 1000, 100) == "--:--"

    def test_seconds(self):
        result = calculate_eta(0, 100, 50)
        assert "s" in result

    def test_minutes(self):
        result = calculate_eta(0, 10000, 10)
        assert ":" in result or "m" in result


class TestFormatSpeed:
    def test_zero(self):
        assert format_speed(0) == "0 B/s"

    def test_kilobytes_per_second(self):
        result = format_speed(1024)
        assert "/s" in result
        assert "KB" in result


class TestGetFileExtension:
    def test_mp4(self):
        assert get_file_extension("video.mp4") == "mp4"

    def test_no_extension(self):
        assert get_file_extension("archivo") == ""

    def test_uppercase_lowercased(self):
        assert get_file_extension("FOTO.JPG") == "jpg"


class TestGetFileIcon:
    def test_mp4_returns_video_icon(self):
        assert get_file_icon("mp4") == "🎬"

    def test_mp3_returns_music_icon(self):
        assert get_file_icon("mp3") == "🎵"

    def test_unknown_returns_folder_icon(self):
        assert get_file_icon("xyz") == "📁"

    def test_pdf(self):
        assert get_file_icon("pdf") == "📕"
