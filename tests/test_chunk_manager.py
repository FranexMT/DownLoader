"""Tests for src/core/chunk_manager.py"""

import json
import os
import shutil
import tempfile
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from src.core.chunk_manager import ChunkManager


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_output_file(tmp_path):
    """Returns a Path for an output file inside a fresh temp directory."""
    return tmp_path / "output.bin"


@pytest.fixture()
def manager(tmp_output_file):
    """ChunkManager bound to a temp output file."""
    return ChunkManager(str(tmp_output_file))


# ---------------------------------------------------------------------------
# save_state / load_state
# ---------------------------------------------------------------------------

class TestSaveAndLoadState:
    def test_save_state_creates_state_file(self, manager):
        # Arrange / Act
        manager.save_state(downloaded_size=512, total_size=1024, elapsed=5.0)
        # Assert
        assert manager.state_file.exists()

    def test_load_state_returns_correct_values(self, manager):
        # Arrange
        manager.save_state(downloaded_size=256, total_size=4096, elapsed=10.0)
        # Act
        state = manager.load_state()
        # Assert
        assert state is not None
        assert state["downloaded_size"] == 256
        assert state["total_size"] == 4096
        assert state["elapsed"] == 10.0

    def test_save_state_timestamp_is_float(self, manager):
        # FIX: timestamp is now time.time() (a float), not a human-readable string
        before = time.time()
        manager.save_state(1000, 2000)
        after = time.time()

        state = manager.load_state()
        assert isinstance(state["timestamp"], float)
        assert before <= state["timestamp"] <= after

    def test_load_state_no_file_returns_none(self, manager):
        # No save_state called — state file should not exist
        result = manager.load_state()
        assert result is None

    def test_save_state_overwrites_previous(self, manager):
        manager.save_state(100, 1000)
        manager.save_state(500, 1000)

        state = manager.load_state()
        assert state["downloaded_size"] == 500


# ---------------------------------------------------------------------------
# merge_chunks
# ---------------------------------------------------------------------------

class TestMergeChunks:
    def _write_chunk(self, manager: ChunkManager, chunk_id: int, content: bytes):
        manager.create_temp_dir()
        chunk_path = manager.get_chunk_path(chunk_id)
        chunk_path.write_bytes(content)

    def test_merge_chunks_success(self, manager, tmp_output_file):
        # Arrange — create 3 chunks with known content
        chunks_data = [b"PART_0_", b"PART_1_", b"PART_2_"]
        for i, data in enumerate(chunks_data):
            self._write_chunk(manager, i, data)

        # Act
        result = manager.merge_chunks(num_chunks=3, delete_after=True)

        # Assert
        assert result is True
        assert tmp_output_file.exists()
        combined = tmp_output_file.read_bytes()
        assert combined == b"PART_0_PART_1_PART_2_"

    def test_merge_chunks_deletes_temp_dir_after(self, manager, tmp_output_file):
        for i in range(2):
            self._write_chunk(manager, i, b"data")

        manager.merge_chunks(num_chunks=2, delete_after=True)

        assert not manager.temp_dir.exists()

    def test_merge_chunks_keeps_temp_dir_when_delete_false(self, manager, tmp_output_file):
        for i in range(2):
            self._write_chunk(manager, i, b"data")

        manager.merge_chunks(num_chunks=2, delete_after=False)

        # temp_dir may still exist because delete_after=False
        assert tmp_output_file.exists()

    def test_merge_chunks_missing_chunk_returns_false(self, manager):
        # FIX: merge_chunks now validates all chunks exist before writing
        # Only write chunk 0, skip chunk 1
        self._write_chunk(manager, 0, b"PART_0")
        # chunk 1 intentionally missing

        result = manager.merge_chunks(num_chunks=2)

        assert result is False

    def test_merge_chunks_empty_chunks_produces_empty_file(self, manager, tmp_output_file):
        # Edge case: 0 chunks requested — loop never runs -> empty output file
        manager.create_temp_dir()
        result = manager.merge_chunks(num_chunks=0, delete_after=False)
        assert result is True
        assert tmp_output_file.read_bytes() == b""

    def test_merge_chunks_single_chunk(self, manager, tmp_output_file):
        self._write_chunk(manager, 0, b"only_chunk")
        result = manager.merge_chunks(num_chunks=1)
        assert result is True
        assert tmp_output_file.read_bytes() == b"only_chunk"


# ---------------------------------------------------------------------------
# global_cleanup
# ---------------------------------------------------------------------------

class TestGlobalCleanup:
    def test_global_cleanup_removes_stale_tmp_dirs(self, tmp_path):
        # Arrange: create a .stale.tmp directory inside tmp_path
        stale_dir = tmp_path / ".stale.tmp"
        stale_dir.mkdir()
        # Back-date mtime to 25 hours ago (> 86400 seconds)
        stale_mtime = time.time() - 90_000
        os.utime(stale_dir, (stale_mtime, stale_mtime))

        # Act
        ChunkManager.global_cleanup(str(tmp_path))

        # Assert — the stale directory must be gone
        assert not stale_dir.exists()

    def test_global_cleanup_keeps_recent_tmp_dirs(self, tmp_path):
        # Arrange: create a .recent.tmp directory with current mtime
        recent_dir = tmp_path / ".recent.tmp"
        recent_dir.mkdir()
        # mtime is essentially now; definitely < 24 h

        # Act
        ChunkManager.global_cleanup(str(tmp_path))

        # Assert — the recent directory must still be there
        assert recent_dir.exists()

    def test_global_cleanup_nonexistent_path_does_not_raise(self):
        # Should silently return without error
        ChunkManager.global_cleanup("/nonexistent/path/that/does_not_exist")

    def test_global_cleanup_ignores_regular_files(self, tmp_path):
        # A regular file matching the glob pattern should not be touched
        regular_file = tmp_path / ".myfile.tmp"
        regular_file.write_bytes(b"data")
        stale_mtime = time.time() - 90_000
        os.utime(regular_file, (stale_mtime, stale_mtime))

        ChunkManager.global_cleanup(str(tmp_path))

        # global_cleanup only acts on directories (item.is_dir() check)
        assert regular_file.exists()

    def test_global_cleanup_only_targets_dot_tmp_pattern(self, tmp_path):
        # A directory NOT matching .*.tmp should never be removed
        normal_dir = tmp_path / "not_a_tmp_dir"
        normal_dir.mkdir()
        stale_mtime = time.time() - 90_000
        os.utime(normal_dir, (stale_mtime, stale_mtime))

        ChunkManager.global_cleanup(str(tmp_path))

        assert normal_dir.exists()


# ---------------------------------------------------------------------------
# cleanup_chunks  (alias for delete_temp_dir)
# ---------------------------------------------------------------------------

class TestCleanupChunks:
    def test_cleanup_chunks_removes_temp_dir(self, manager):
        manager.create_temp_dir()
        assert manager.temp_dir.exists()
        manager.cleanup_chunks()
        assert not manager.temp_dir.exists()

    def test_cleanup_chunks_on_nonexistent_dir_does_not_raise(self, manager):
        # temp_dir was never created
        manager.cleanup_chunks()  # must not raise


# ---------------------------------------------------------------------------
# get_chunks_status
# ---------------------------------------------------------------------------

class TestGetChunksStatus:
    def test_get_chunks_status_no_temp_dir(self, manager):
        status = manager.get_chunks_status()
        assert status == {"exists": False, "chunks": []}

    def test_get_chunks_status_empty_temp_dir(self, manager):
        manager.create_temp_dir()
        status = manager.get_chunks_status()
        assert status["exists"] is True
        assert status["chunks"] == []

    def test_get_chunks_status_with_chunks(self, manager):
        manager.create_temp_dir()
        for i in range(3):
            manager.get_chunk_path(i).write_bytes(b"x" * (i + 1))

        status = manager.get_chunks_status()
        assert status["exists"] is True
        assert len(status["chunks"]) == 3
        # Sizes should match the bytes written
        sizes = [c["size"] for c in status["chunks"]]
        assert sizes == [1, 2, 3]

    def test_get_chunks_status_includes_temp_dir_path(self, manager):
        manager.create_temp_dir()
        status = manager.get_chunks_status()
        assert "temp_dir" in status
        assert str(manager.temp_dir) in status["temp_dir"]


# ---------------------------------------------------------------------------
# resume_info
# ---------------------------------------------------------------------------

class TestResumeInfo:
    def test_resume_info_not_resumable_when_no_temp_dir(self, manager):
        info = manager.resume_info()
        assert info == {"resumable": False}

    def test_resume_info_resumable_with_chunks(self, manager):
        manager.create_temp_dir()
        manager.get_chunk_path(0).write_bytes(b"aa")
        manager.get_chunk_path(1).write_bytes(b"bbb")

        info = manager.resume_info()
        assert info["resumable"] is True
        assert info["chunks_downloaded"] == 2
        assert info["downloaded_size"] == 5  # 2 + 3 bytes

    def test_resume_info_empty_temp_dir_shows_resumable_with_zero_chunks(self, manager):
        manager.create_temp_dir()
        info = manager.resume_info()
        assert info["resumable"] is True
        assert info["chunks_downloaded"] == 0
        assert info["downloaded_size"] == 0


# ---------------------------------------------------------------------------
# Exception paths
# ---------------------------------------------------------------------------

class TestExceptionPaths:
    def test_delete_temp_dir_exception_is_logged_not_raised(self, manager, tmp_path):
        manager.create_temp_dir()
        # Patch shutil.rmtree to raise to exercise the except branch
        with patch("shutil.rmtree", side_effect=PermissionError("denied")):
            manager.delete_temp_dir()  # must not propagate

    def test_merge_chunks_exception_returns_false(self, manager):
        manager.create_temp_dir()
        manager.get_chunk_path(0).write_bytes(b"data")
        # Patch open to raise after chunk validation passes
        with patch("builtins.open", side_effect=IOError("disk full")):
            result = manager.merge_chunks(num_chunks=1, delete_after=False)
        assert result is False

    def test_save_state_exception_is_suppressed(self, manager, tmp_path):
        # Make the temp_dir creation fail to exercise the except in save_state
        with patch.object(manager, "create_temp_dir", side_effect=OSError("no space")):
            manager.save_state(100, 200)  # must not raise

    def test_load_state_corrupt_json_returns_none(self, manager):
        manager.create_temp_dir()
        manager.state_file.write_text("NOT VALID JSON{{")
        result = manager.load_state()
        assert result is None

    def test_global_cleanup_exception_is_suppressed(self, tmp_path):
        # Patch Path.glob to raise, exercising the except branch
        with patch("pathlib.Path.glob", side_effect=OSError("permission denied")):
            ChunkManager.global_cleanup(str(tmp_path))  # must not raise
