"""Tests for src/utils/validators.py"""

import hashlib
import tempfile
import os
import pytest

from src.utils.validators import (
    is_valid_url,
    verify_checksum,
    sanitize_filename,
    extract_filename_from_url,
    get_file_hash,
    is_supported_url,
)


# ---------------------------------------------------------------------------
# is_valid_url
# ---------------------------------------------------------------------------

class TestIsValidUrl:
    def test_is_valid_url_with_http(self):
        # Arrange / Act / Assert
        assert is_valid_url("http://example.com") is True

    def test_is_valid_url_with_https(self):
        assert is_valid_url("https://example.com/path/to/file.zip") is True

    def test_is_valid_url_with_https_query(self):
        assert is_valid_url("https://cdn.example.com/file.tar.gz?token=abc123") is True

    def test_is_valid_url_with_ip_address(self):
        assert is_valid_url("http://192.168.1.1/resource") is True

    def test_is_valid_url_with_port(self):
        assert is_valid_url("http://example.com:8080/file") is True

    def test_is_valid_url_with_invalid_scheme(self):
        # ftp is not in the allowed set (http/https only)
        assert is_valid_url("ftp://example.com/file") is False

    def test_is_valid_url_without_scheme(self):
        assert is_valid_url("example.com/file") is False

    def test_is_valid_url_empty_string(self):
        assert is_valid_url("") is False

    def test_is_valid_url_none(self):
        assert is_valid_url(None) is False

    def test_is_valid_url_non_string_type(self):
        assert is_valid_url(12345) is False

    def test_is_valid_url_malformed_no_netloc(self):
        # urlparse("https://") gives scheme='https' but empty netloc
        assert is_valid_url("https://") is False

    def test_is_valid_url_just_path(self):
        assert is_valid_url("/usr/local/file.tar.gz") is False


# ---------------------------------------------------------------------------
# verify_checksum
# ---------------------------------------------------------------------------

class TestVerifyChecksum:
    @pytest.fixture()
    def temp_file_with_content(self, tmp_path):
        """Creates a temp file with known content and returns (path, sha256)."""
        content = b"hello downloader world"
        fpath = tmp_path / "sample.bin"
        fpath.write_bytes(content)
        expected_hash = hashlib.sha256(content).hexdigest()
        return str(fpath), expected_hash

    def test_verify_checksum_sha256_valid(self, temp_file_with_content):
        # Arrange
        filepath, expected = temp_file_with_content
        # Act
        result = verify_checksum(filepath, expected, algorithm="sha256")
        # Assert
        assert result is True

    def test_verify_checksum_case_insensitive(self, temp_file_with_content):
        filepath, expected = temp_file_with_content
        assert verify_checksum(filepath, expected.upper()) is True

    def test_verify_checksum_md5_valid(self, tmp_path):
        content = b"test md5 content"
        fpath = tmp_path / "md5_file.bin"
        fpath.write_bytes(content)
        expected = hashlib.md5(content).hexdigest()
        assert verify_checksum(str(fpath), expected, algorithm="md5") is True

    def test_verify_checksum_invalid(self, temp_file_with_content):
        # Arrange
        filepath, _ = temp_file_with_content
        wrong_hash = "0" * 64
        # Act
        result = verify_checksum(filepath, wrong_hash)
        # Assert
        assert result is False

    def test_verify_checksum_empty_expected_returns_true(self, temp_file_with_content):
        # When no checksum is provided verification is skipped -> True
        filepath, _ = temp_file_with_content
        assert verify_checksum(filepath, "") is True

    def test_verify_checksum_none_expected_returns_true(self, temp_file_with_content):
        filepath, _ = temp_file_with_content
        assert verify_checksum(filepath, None) is True

    def test_verify_checksum_file_not_found(self):
        # FIX verified: missing file returns False (not True)
        result = verify_checksum("/nonexistent/path/to/file.bin", "abc123")
        assert result is False

    def test_verify_checksum_unknown_algorithm_returns_true(self, temp_file_with_content):
        # Unknown algorithm -> ValueError caught -> returns True (no check performed)
        filepath, _ = temp_file_with_content
        assert verify_checksum(filepath, "abc", algorithm="not_a_real_algo") is True


# ---------------------------------------------------------------------------
# sanitize_filename
# ---------------------------------------------------------------------------

class TestSanitizeFilename:
    def test_sanitize_filename_removes_invalid_chars(self):
        # Arrange
        dirty = 'file<>:"/\\|?*.txt'
        # Act
        result = sanitize_filename(dirty)
        # Assert — none of the forbidden characters should remain
        for ch in '<>:"/\\|?*':
            assert ch not in result

    def test_sanitize_filename_strips_leading_trailing_dots_spaces(self):
        result = sanitize_filename("  ..myfile.zip.. ")
        assert not result.startswith((".", " "))
        assert not result.endswith((".", " "))

    def test_sanitize_filename_truncates_long_name(self):
        long_name = "a" * 300 + ".txt"
        result = sanitize_filename(long_name)
        assert len(result) <= 200

    def test_sanitize_filename_truncates_long_name_no_extension(self):
        long_name = "b" * 300
        result = sanitize_filename(long_name)
        assert len(result) <= 200

    def test_sanitize_filename_empty_string_returns_default(self):
        result = sanitize_filename("")
        assert result == "download"

    def test_sanitize_filename_only_invalid_chars_returns_default(self):
        # After stripping '. ' the filename could be empty
        result = sanitize_filename("...")
        assert result == "download"

    def test_sanitize_filename_normal_name_unchanged(self):
        result = sanitize_filename("normal_file-v1.2.tar.gz")
        assert result == "normal_file-v1.2.tar.gz"


# ---------------------------------------------------------------------------
# extract_filename_from_url
# ---------------------------------------------------------------------------

class TestExtractFilenameFromUrl:
    def test_extract_filename_from_url_path(self):
        url = "https://example.com/downloads/archive.zip"
        result = extract_filename_from_url(url)
        assert result == "archive.zip"

    def test_extract_filename_from_url_no_path_returns_default(self):
        url = "https://example.com/"
        result = extract_filename_from_url(url)
        assert result == "download"

    def test_extract_filename_from_url_content_disposition(self):
        url = "https://example.com/some_path"
        headers = {"content-disposition": 'attachment; filename="my_report.pdf"'}
        result = extract_filename_from_url(url, headers)
        assert result == "my_report.pdf"

    def test_extract_filename_from_url_content_disposition_no_quotes(self):
        url = "https://example.com/file"
        headers = {"content-disposition": "attachment; filename=report.csv"}
        result = extract_filename_from_url(url, headers)
        assert result == "report.csv"

    def test_extract_filename_from_url_prefers_content_disposition(self):
        # Content-Disposition should take priority over URL path
        url = "https://example.com/downloads/ignored.zip"
        headers = {"content-disposition": 'attachment; filename="preferred.zip"'}
        result = extract_filename_from_url(url, headers)
        assert result == "preferred.zip"

    def test_extract_filename_sanitizes_result(self):
        url = "https://example.com/file<invalid>.txt"
        result = extract_filename_from_url(url)
        assert "<" not in result
        assert ">" not in result

    def test_extract_filename_url_with_query_string(self):
        # Path segment should be extracted; query string is not part of the filename
        url = "https://example.com/path/data.json?v=1&token=xyz"
        result = extract_filename_from_url(url)
        assert result == "data.json"

    def test_extract_filename_no_headers(self):
        url = "https://example.com/video.mp4"
        result = extract_filename_from_url(url, headers=None)
        assert result == "video.mp4"


# ---------------------------------------------------------------------------
# get_file_hash
# ---------------------------------------------------------------------------

class TestGetFileHash:
    def test_get_file_hash_matches_manual_sha256(self, tmp_path):
        content = b"downloader hash test"
        fpath = tmp_path / "file.bin"
        fpath.write_bytes(content)
        expected = hashlib.sha256(content).hexdigest()
        assert get_file_hash(str(fpath)) == expected

    def test_get_file_hash_md5(self, tmp_path):
        content = b"md5 content"
        fpath = tmp_path / "md5.bin"
        fpath.write_bytes(content)
        expected = hashlib.md5(content).hexdigest()
        assert get_file_hash(str(fpath), algorithm="md5") == expected

    def test_get_file_hash_missing_file_returns_empty(self):
        result = get_file_hash("/nonexistent/file.bin")
        assert result == ""

    def test_get_file_hash_empty_file(self, tmp_path):
        fpath = tmp_path / "empty.bin"
        fpath.write_bytes(b"")
        result = get_file_hash(str(fpath))
        assert result == hashlib.sha256(b"").hexdigest()


# ---------------------------------------------------------------------------
# is_supported_url
# ---------------------------------------------------------------------------

class TestIsSupportedUrl:
    def test_is_supported_url_http(self):
        assert is_supported_url("http://example.com/file") is True

    def test_is_supported_url_https(self):
        assert is_supported_url("https://example.com/file") is True

    def test_is_supported_url_ftp_returns_false(self):
        assert is_supported_url("ftp://example.com/file") is False

    def test_is_supported_url_empty_returns_false(self):
        assert is_supported_url("") is False

    def test_is_supported_url_none_returns_false(self):
        assert is_supported_url(None) is False
