import sqlite3
import os
import time
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime
import logging

from ..utils.validators import extract_filename_from_url

logger = logging.getLogger(__name__)


class Database:
    """Gestor de base de datos SQLite para el historial."""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            home = Path.home()
            config_dir = home / ".downloader"
            config_dir.mkdir(parents=True, exist_ok=True)
            db_path = config_dir / "data.db"
        
        self.db_path = str(db_path)
        self._init_db()
    
    def _init_db(self):
        """Inicializa la base de datos."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS downloads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    title TEXT,
                    thumbnail TEXT,
                    filename TEXT NOT NULL,
                    destination TEXT NOT NULL,
                    total_size INTEGER DEFAULT 0,
                    downloaded_size INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'PENDING',
                    speed REAL DEFAULT 0,
                    start_time REAL,
                    end_time REAL,
                    error_message TEXT,
                    checksum TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Migraciones: Agregar columnas si no existen
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(downloads)")
            columns = [c[1] for c in cursor.fetchall()]
            
            if "title" not in columns:
                cursor.execute("ALTER TABLE downloads ADD COLUMN title TEXT")
            if "thumbnail" not in columns:
                cursor.execute("ALTER TABLE downloads ADD COLUMN thumbnail TEXT")
            
            conn.commit()
    
    def create_download(self, url: str, filename: str, destination: str, title: str = None, thumbnail: str = None) -> int:
        """Crea un nuevo registro de descarga."""
        if filename == "pending":
            filename = extract_filename_from_url(url)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO downloads (url, filename, destination, status, start_time, title, thumbnail)
                VALUES (?, ?, ?, 'PENDING', ?, ?, ?)
            """, (url, filename, destination, time.time(), title, thumbnail))
            conn.commit()
            return cursor.lastrowid
    
    def update_download(self, download_id: int, **kwargs):
        """Actualiza campos de una descarga."""
        allowed_fields = [
            'filename', 'destination', 'total_size', 'downloaded_size',
            'status', 'speed', 'end_time', 'error_message', 'checksum',
            'title', 'thumbnail'
        ]
        
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if not updates:
            return
        
        updates['updated_at'] = datetime.utcnow().isoformat()
        
        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [download_id]
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(f"""
                UPDATE downloads SET {set_clause} WHERE id = ?
            """, values)
            conn.commit()
    
    def get_download(self, download_id: int) -> Optional[Dict]:
        """Obtiene una descarga por ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM downloads WHERE id = ?", (download_id,))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
    
    def get_all_downloads(self, status: str = None) -> List[Dict]:
        """Obtiene todas las descargas, opcionalmente filtradas por status."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            if status is None:
                cursor = conn.execute(
                    "SELECT * FROM downloads ORDER BY created_at DESC",
                )
            else:
                cursor = conn.execute(
                    "SELECT * FROM downloads WHERE status = ? ORDER BY created_at DESC",
                    (status,)
                )
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_active_downloads(self) -> List[Dict]:
        """Obtiene descargas activas (DOWNLOADING, PAUSED)."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM downloads 
                WHERE status IN ('PENDING', 'DOWNLOADING', 'PAUSED')
                ORDER BY created_at DESC
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_completed_downloads(self) -> List[Dict]:
        """Obtiene descargas completadas."""
        return self.get_all_downloads(status='COMPLETED')
    
    def delete_download(self, download_id: int) -> bool:
        """Elimina una descarga."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM downloads WHERE id = ?", (download_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def clear_history(self, status: str = None) -> int:
        """Limpia el historial."""
        with sqlite3.connect(self.db_path) as conn:
            if status:
                cursor = conn.execute(
                    "DELETE FROM downloads WHERE status = ?",
                    (status,)
                )
            else:
                cursor = conn.execute("DELETE FROM downloads")
            conn.commit()
            return cursor.rowcount
    
    def get_statistics(self) -> Dict:
        """Obtiene estadísticas del historial."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'COMPLETED' THEN 1 ELSE 0 END) as completed,
                    SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) as failed,
                    SUM(total_size) as total_bytes
                FROM downloads
            """)
            row = cursor.fetchone()
            
            return {
                "total": row[0] or 0,
                "completed": row[1] or 0,
                "failed": row[2] or 0,
                "total_bytes": row[3] or 0
            }


db = Database()
