import pytest
from src.utils.validators import (
    is_valid_url,
    extract_filename_from_url,
    sanitize_filename,
    verify_checksum,
)


class TestIsValidUrl:
    def test_valid_http_url(self):
        assert is_valid_url("http://example.com/file.zip") is True

    def test_valid_https_url(self):
        assert is_valid_url("https://example.com/file.zip") is True

    def test_invalid_no_scheme(self):
        assert is_valid_url("example.com/file.zip") is False

    def test_invalid_ftp_scheme(self):
        assert is_valid_url("ftp://example.com/file.zip") is False

    def test_empty_string(self):
        assert is_valid_url("") is False

    def test_none(self):
        assert is_valid_url(None) is False

    def test_just_scheme(self):
        assert is_valid_url("https://") is False


class TestExtractFilenameFromUrl:
    def test_from_path(self):
        assert extract_filename_from_url("https://example.com/path/file.zip") == "file.zip"

    def test_from_content_disposition(self):
        headers = {"content-disposition": 'attachment; filename="report.pdf"'}
        assert extract_filename_from_url("https://example.com/dl", headers) == "report.pdf"

    def test_fallback_when_no_filename(self):
        result = extract_filename_from_url("https://example.com/")
        assert result == "download"

    def test_no_headers(self):
        result = extract_filename_from_url("https://example.com/data.csv")
        assert result == "data.csv"


class TestSanitizeFilename:
    def test_removes_invalid_chars(self):
        result = sanitize_filename('file<>:"/\\|?*.txt')
        assert "<" not in result
        assert ">" not in result
        assert ":" not in result

    def test_strips_leading_dots_and_spaces(self):
        result = sanitize_filename("  ..file.txt")
        assert not result.startswith(".")
        assert not result.startswith(" ")

    def test_empty_becomes_download(self):
        result = sanitize_filename("")
        assert result == "download"

    def test_truncates_long_names(self):
        long_name = "a" * 250 + ".txt"
        result = sanitize_filename(long_name)
        assert len(result) <= 200

    def test_normal_name_unchanged(self):
        assert sanitize_filename("archivo_normal.mp4") == "archivo_normal.mp4"


class TestVerifyChecksum:
    def test_empty_expected_returns_true(self, tmp_path):
        f = tmp_path / "file.bin"
        f.write_bytes(b"contenido")
        assert verify_checksum(str(f), "") is True

    def test_correct_checksum(self, tmp_path):
        import hashlib
        content = b"hola mundo"
        f = tmp_path / "file.bin"
        f.write_bytes(content)
        expected = hashlib.sha256(content).hexdigest()
        assert verify_checksum(str(f), expected, "sha256") is True

    def test_wrong_checksum(self, tmp_path):
        f = tmp_path / "file.bin"
        f.write_bytes(b"hola mundo")
        assert verify_checksum(str(f), "abc123deadbeef", "sha256") is False

    def test_missing_file_returns_false(self, tmp_path):
        assert verify_checksum(str(tmp_path / "noexiste.bin"), "abc123") is False
