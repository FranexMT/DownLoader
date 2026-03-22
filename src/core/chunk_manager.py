import os
import shutil
import json
import time
from pathlib import Path
from typing import List, Optional, Dict
import logging

logger = logging.getLogger(__name__)


class ChunkManager:
    """Gestor de fragmentos para descargas multithread."""

    def __init__(self, output_path: str):
        self.output_path = Path(output_path)
        self.temp_dir = self.output_path.parent / f".{self.output_path.stem}.tmp"
        self.state_file = self.temp_dir / "state.json"

    def get_chunk_path(self, chunk_id: int) -> Path:
        """Retorna la ruta del fragmento."""
        return self.temp_dir / f"part_{chunk_id}"

    def create_temp_dir(self):
        """Crea el directorio temporal."""
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def delete_temp_dir(self):
        """Elimina el directorio temporal."""
        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
        except Exception as e:
            logger.warning(f"Error al eliminar directorio temporal: {e}")

    def merge_chunks(self, num_chunks: int, delete_after: bool = True) -> bool:
        """Une todos los fragmentos en un solo archivo."""
        try:
            # Validate that every chunk exists before writing anything,
            # to prevent silent file corruption from incomplete downloads.
            missing = [
                self.get_chunk_path(i)
                for i in range(num_chunks)
                if not self.get_chunk_path(i).exists()
            ]
            if missing:
                logger.error(
                    f"Faltan {len(missing)} fragmento(s) — merge abortado: "
                    + ", ".join(str(p) for p in missing)
                )
                return False

            with open(self.output_path, "wb") as outfile:
                for i in range(num_chunks):
                    chunk_path = self.get_chunk_path(i)
                    with open(chunk_path, "rb") as infile:
                        shutil.copyfileobj(infile, outfile)

                    if delete_after:
                        chunk_path.unlink()

            if delete_after:
                self.delete_temp_dir()

            logger.info(f"Archivo fusionado: {self.output_path}")
            return True

        except Exception as e:
            logger.error(f"Error al fusionar fragmentos: {e}")
            return False

    def cleanup_chunks(self):
        """Limpia los fragmentos temporales."""
        self.delete_temp_dir()

    def get_chunks_status(self) -> dict:
        """Retorna el estado de los fragmentos."""
        if not self.temp_dir.exists():
            return {"exists": False, "chunks": []}

        chunks = []
        for chunk_file in sorted(self.temp_dir.glob("part_*")):
            chunks.append({"name": chunk_file.name, "size": chunk_file.stat().st_size})

        return {"exists": True, "temp_dir": str(self.temp_dir), "chunks": chunks}

    def resume_info(self) -> dict:
        """Retorna información para reanudar descarga."""
        status = self.get_chunks_status()
        if not status["exists"]:
            return {"resumable": False}

        downloaded_chunks = 0
        total_chunk_size = 0

        for chunk in status["chunks"]:
            downloaded_chunks += 1
            total_chunk_size += chunk["size"]

        return {
            "resumable": True,
            "chunks_downloaded": downloaded_chunks,
            "total_chunks": len(status["chunks"]),
            "downloaded_size": total_chunk_size,
        }

    def save_state(self, downloaded_size: int, total_size: int, elapsed: float = 0):
        """Guarda el estado de la descarga para permitir resume real."""
        try:
            self.create_temp_dir()
            state = {
                "downloaded_size": downloaded_size,
                "total_size": total_size,
                "elapsed": elapsed,
                "timestamp": time.time(),
            }
            with open(self.state_file, "w") as f:
                json.dump(state, f)
        except Exception as e:
            logger.warning(f"Error guardando estado: {e}")

    def load_state(self) -> Optional[Dict]:
        """Carga el estado guardado de una descarga."""
        try:
            if self.state_file.exists():
                with open(self.state_file, "r") as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Error cargando estado: {e}")
        return None

    @staticmethod
    def global_cleanup(download_path: str):
        """Limpia directorios temporales huérfanos en la ruta de descarga."""
        try:
            path = Path(download_path)
            if not path.exists():
                return
            
            for item in path.glob(".*.tmp"):
                if item.is_dir():
                    # Si el directorio no ha sido modificado en más de 24 horas, lo eliminamos
                    # Esto evita borrar descargas activas en curso
                    mtime = item.stat().st_mtime
                    if (time.time() - mtime) > 86400:
                        logger.info(f"Limpiando directorio temporal huérfano: {item}")
                        shutil.rmtree(item)
        except Exception as e:
            logger.warning(f"Error en limpieza global: {e}")
