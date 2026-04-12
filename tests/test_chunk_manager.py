import pytest
import json
from pathlib import Path
from src.core.chunk_manager import ChunkManager


@pytest.fixture
def cm(tmp_path):
    output = tmp_path / "output.bin"
    return ChunkManager(str(output))


class TestChunkManagerPaths:
    def test_chunk_path_naming(self, cm):
        p = cm.get_chunk_path(0)
        assert p.name == "part_0"

    def test_temp_dir_naming(self, cm, tmp_path):
        assert cm.temp_dir.name.startswith(".")
        assert cm.temp_dir.name.endswith(".tmp")


class TestChunkManagerTempDir:
    def test_create_temp_dir(self, cm):
        cm.create_temp_dir()
        assert cm.temp_dir.exists()

    def test_delete_temp_dir(self, cm):
        cm.create_temp_dir()
        cm.delete_temp_dir()
        assert not cm.temp_dir.exists()

    def test_cleanup_chunks(self, cm):
        cm.create_temp_dir()
        cm.cleanup_chunks()
        assert not cm.temp_dir.exists()


class TestChunkManagerMerge:
    def test_merge_single_chunk(self, cm):
        cm.create_temp_dir()
        chunk = cm.get_chunk_path(0)
        chunk.write_bytes(b"hola mundo")
        result = cm.merge_chunks(1)
        assert result is True
        assert cm.output_path.read_bytes() == b"hola mundo"

    def test_merge_multiple_chunks(self, cm):
        cm.create_temp_dir()
        for i, data in enumerate([b"parte1_", b"parte2_", b"parte3"]):
            cm.get_chunk_path(i).write_bytes(data)
        result = cm.merge_chunks(3)
        assert result is True
        assert cm.output_path.read_bytes() == b"parte1_parte2_parte3"

    def test_merge_missing_chunk_returns_false(self, cm):
        cm.create_temp_dir()
        # Solo creamos el chunk 0, falta el 1
        cm.get_chunk_path(0).write_bytes(b"solo un chunk")
        result = cm.merge_chunks(2)
        assert result is False


class TestChunkManagerState:
    def test_save_and_load_state(self, cm):
        cm.create_temp_dir()
        cm.save_state(500, 1000, 2.5)
        state = cm.load_state()
        assert state["downloaded_size"] == 500
        assert state["total_size"] == 1000
        assert state["elapsed"] == 2.5

    def test_load_state_no_file_returns_none(self, cm):
        assert cm.load_state() is None

    def test_resume_info_no_dir(self, cm):
        info = cm.resume_info()
        assert info["resumable"] is False

    def test_resume_info_with_chunks(self, cm):
        cm.create_temp_dir()
        cm.get_chunk_path(0).write_bytes(b"datos")
        info = cm.resume_info()
        assert info["resumable"] is True
        assert info["chunks_downloaded"] == 1


class TestGlobalCleanup:
    def test_does_not_crash_on_missing_path(self, tmp_path):
        ChunkManager.global_cleanup(str(tmp_path / "inexistente"))
