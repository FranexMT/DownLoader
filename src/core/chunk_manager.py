import os
import shutil
from pathlib import Path
from typing import List
import logging

logger = logging.getLogger(__name__)


class ChunkManager:
    """Gestor de fragmentos para descargas multithread."""
    
    def __init__(self, output_path: str):
        self.output_path = Path(output_path)
        self.temp_dir = self.output_path.parent / f".{self.output_path.stem}.tmp"
    
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
            with open(self.output_path, 'wb') as outfile:
                for i in range(num_chunks):
                    chunk_path = self.get_chunk_path(i)
                    if chunk_path.exists():
                        with open(chunk_path, 'rb') as infile:
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
            chunks.append({
                "name": chunk_file.name,
                "size": chunk_file.stat().st_size
            })
        
        return {
            "exists": True,
            "temp_dir": str(self.temp_dir),
            "chunks": chunks
        }
    
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
            "downloaded_size": total_chunk_size
        }
