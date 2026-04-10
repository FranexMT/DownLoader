"""Fixtures compartidos para todas las pruebas."""

import pytest
import tempfile
import os
from pathlib import Path

from src.core.database import Database


@pytest.fixture(scope="function")
def tmp_db(tmp_path):
    """Base de datos temporal en archivo para cada test."""
    db_file = tmp_path / "test.db"
    return Database(db_path=str(db_file))


@pytest.fixture(scope="function")
def tmp_download_dir(tmp_path):
    """Directorio temporal para descargas."""
    download_dir = tmp_path / "downloads"
    download_dir.mkdir()
    return download_dir


@pytest.fixture(scope="function")
def sample_file(tmp_path):
    """Archivo de muestra con contenido conocido."""
    content = b"DownLoader Pro test content - sample file for testing"
    filepath = tmp_path / "sample.bin"
    filepath.write_bytes(content)
    return filepath, content
