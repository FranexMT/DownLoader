import os
import time
import threading
import requests
import logging
from pathlib import Path
from typing import Optional, Callable
from .config import load_config
from .chunk_manager import ChunkManager
from .database import db
from ..utils.validators import is_valid_url, extract_filename_from_url, sanitize_filename

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DownloadTask:
    """Representa una tarea de descarga."""
    
    STATUS_PENDING = "PENDING"
    STATUS_DOWNLOADING = "DOWNLOADING"
    STATUS_PAUSED = "PAUSED"
    STATUS_COMPLETED = "COMPLETED"
    STATUS_FAILED = "FAILED"
    STATUS_CANCELLED = "CANCELLED"
    
    def __init__(self, task_id: int, url: str, destination: str, num_threads: int = None):
        self.id = task_id
        self.url = url
        self.destination = Path(destination)
        self.num_threads = num_threads or load_config()["default_threads"]
        
        self.status = self.STATUS_PENDING
        self.progress = 0.0
        self.total_size = 0
        self.downloaded_size = 0
        self.speed = 0.0
        self.error = None
        
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()
        
        self.chunk_manager = None
        self.output_file = None
        
    def stop(self):
        """Detiene la descarga."""
        self._stop_event.set()
        self._pause_event.set()
        
    def pause(self):
        """Pausa la descarga."""
        if self.status == self.STATUS_DOWNLOADING:
            self.status = self.STATUS_PAUSED
            self._pause_event.clear()
            db.update_download(self.id, status=self.STATUS_PAUSED)
            
    def resume(self):
        """Reanuda la descarga."""
        if self.status == self.STATUS_PAUSED:
            self.status = self.STATUS_DOWNLOADING
            self._pause_event.set()
            db.update_download(self.id, status=self.STATUS_DOWNLOADING)


class Downloader:
    """Motor de descargas con soporte para multithreading y pause/resume."""
    
    def __init__(self):
        self.config = load_config()
        self.tasks = {}
        self.task_lock = threading.Lock()
        self._callbacks = {}
        
    def set_progress_callback(self, task_id: int, callback: Callable):
        """Establece callback para progreso."""
        self._callbacks[task_id] = callback
        
    def create_task(self, url: str, destination: str = None) -> Optional[DownloadTask]:
        """Crea una nueva tarea de descarga."""
        if not is_valid_url(url):
            logger.error(f"URL inválida: {url}")
            return None
        
        destination = destination or self.config["default_download_path"]
        dest_path = Path(destination)
        dest_path.mkdir(parents=True, exist_ok=True)
        
        with self.task_lock:
            task_id = db.create_download(url, "pending", str(dest_path))
            
        task = DownloadTask(task_id, url, dest_path, self.config["default_threads"])
        self.tasks[task_id] = task
        
        return task
    
    def start_download(self, task_id: int) -> bool:
        """Inicia la descarga."""
        task = self.tasks.get(task_id)
        if not task:
            return False
        
        try:
            task.status = DownloadTask.STATUS_DOWNLOADING
            db.update_download(task_id, status=DownloadTask.STATUS_DOWNLOADING, start_time=time.time())
            
            with requests.head(task.url, allow_redirects=True, timeout=self.config["timeout"]) as response:
                task.total_size = int(response.headers.get('content-length', 0))
                accept_ranges = response.headers.get('accept-ranges', 'none')
                
                supports_resume = accept_ranges.lower() == 'bytes'
                
                filename = extract_filename_from_url(task.url, dict(response.headers))
                task.output_file = task.destination / sanitize_filename(filename)
                
                db.update_download(task_id, filename=str(task.output_file), total_size=task.total_size)
            
            if task.total_size == 0:
                task.status = DownloadTask.STATUS_FAILED
                task.error = "No se pudo obtener el tamaño del archivo"
                db.update_download(task_id, status=task.STATUS_FAILED, error_message=task.error)
                return False
            
            if task.total_size < 1024 * 1024 * 10 or task.num_threads == 1:
                self._download_single(task)
            else:
                self._download_multithread(task, supports_resume)
            
            if task.status == DownloadTask.STATUS_DOWNLOADING:
                task.status = DownloadTask.STATUS_COMPLETED
                task.progress = 100.0
                db.update_download(task_id, status=DownloadTask.STATUS_COMPLETED, 
                                 downloaded_size=task.total_size, end_time=time.time())
            
            return task.status == DownloadTask.STATUS_COMPLETED
            
        except Exception as e:
            task.status = DownloadTask.STATUS_FAILED
            task.error = str(e)
            logger.error(f"Error en descarga {task_id}: {e}")
            db.update_download(task_id, status=task.STATUS_FAILED, error_message=str(e))
            return False
    
    def _download_single(self, task: DownloadTask):
        """Descarga con un solo hilo."""
        try:
            task.chunk_manager = ChunkManager(str(task.output_file))
            task.chunk_manager.create_temp_dir()
            
            with requests.get(task.url, stream=True, timeout=self.config["timeout"]) as response:
                response.raise_for_status()
                
                mode = 'wb'
                chunk_path = task.chunk_manager.get_chunk_path(0)
                downloaded = 0
                start_time = time.time()
                
                with open(chunk_path, mode) as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if task._stop_event.is_set():
                            task.status = DownloadTask.STATUS_CANCELLED
                            db.update_download(task.id, status=task.STATUS_CANCELLED)
                            break
                        
                        task._pause_event.wait()
                        
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            task.downloaded_size = downloaded
                            task.progress = (downloaded / task.total_size) * 100
                            
                            elapsed = time.time() - start_time
                            if elapsed > 0:
                                task.speed = downloaded / elapsed
                            
                            db.update_download(task.id, downloaded_size=downloaded, speed=task.speed)
                            
                            if task.id in self._callbacks:
                                self._callbacks[task.id](task.progress, task.speed)
            
            if task.status == DownloadTask.STATUS_DOWNLOADING:
                task.chunk_manager.merge_chunks(1)
                
        except Exception as e:
            task.error = str(e)
            task.status = DownloadTask.STATUS_FAILED
            db.update_download(task.id, status=task.STATUS_FAILED, error_message=str(e))
    
    def _download_multithread(self, task: DownloadTask, supports_resume: bool):
        """Descarga con múltiples hilos."""
        chunk_size = task.total_size // task.num_threads
        ranges = []
        
        for i in range(task.num_threads):
            start = i * chunk_size
            end = start + chunk_size - 1 if i < task.num_threads - 1 else task.total_size - 1
            ranges.append((start, end))
        
        task.chunk_manager = ChunkManager(str(task.output_file))
        
        if supports_resume:
            resume_info = task.chunk_manager.resume_info()
            if resume_info.get("resumable"):
                logger.info(f"Reanudando descarga con {resume_info['chunks_downloaded']} chunks")
        else:
            task.chunk_manager.create_temp_dir()
        
        if not task.chunk_manager.temp_dir.exists():
            task.chunk_manager.create_temp_dir()
        
        threads = []
        downloaded_bytes = [0] * task.num_threads
        lock = threading.Lock()
        
        def download_chunk(start: int, end: int, thread_id: int):
            if task._stop_event.is_set():
                return
            
            headers = {'Range': f'bytes={start}-{end}'}
            chunk_path = task.chunk_manager.get_chunk_path(thread_id)
            
            existing_size = 0
            if chunk_path.exists():
                existing_size = chunk_path.stat().st_size
                if existing_size >= (end - start + 1):
                    with lock:
                        downloaded_bytes[thread_id] = existing_size
                    return
                headers['Range'] = f'bytes={start + existing_size}-{end}'
            
            try:
                response = requests.get(task.url, headers=headers, stream=True, timeout=self.config["timeout"])
                response.raise_for_status()
                
                mode = 'ab' if existing_size > 0 else 'wb'
                with open(chunk_path, mode) as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if task._stop_event.is_set():
                            break
                        
                        task._pause_event.wait()
                        
                        if chunk:
                            f.write(chunk)
                            with lock:
                                downloaded_bytes[thread_id] += len(chunk)
                                task.downloaded_size = sum(downloaded_bytes)
                                task.progress = (task.downloaded_size / task.total_size) * 100
                                
                                if task.id in self._callbacks:
                                    self._callbacks[task.id](task.progress, task.speed)
            except Exception as e:
                logger.error(f"Error en hilo {thread_id}: {e}")
        
        start_time = time.time()
        
        for i, (start, end) in enumerate(ranges):
            t = threading.Thread(target=download_chunk, args=(start, end, i))
            threads.append(t)
            t.start()
        
        while any(t.is_alive() for t in threads):
            if task._stop_event.is_set():
                break
            time.sleep(0.1)
            
            elapsed = time.time() - start_time
            if elapsed > 0:
                task.speed = task.downloaded_size / elapsed
            
            db.update_download(task.id, downloaded_size=task.downloaded_size, speed=task.speed)
        
        for t in threads:
            t.join()
        
        if task.status != DownloadTask.STATUS_CANCELLED and task.status != DownloadTask.STATUS_FAILED:
            task.chunk_manager.merge_chunks(task.num_threads)
    
    def pause_task(self, task_id: int) -> bool:
        """Pausa una tarea."""
        task = self.tasks.get(task_id)
        if task:
            task.pause()
            return True
        return False
    
    def resume_task(self, task_id: int) -> bool:
        """Reanuda una tarea."""
        task = self.tasks.get(task_id)
        if task:
            task.resume()
            thread = threading.Thread(target=self.start_download, args=(task_id,))
            thread.start()
            return True
        return False
    
    def cancel_task(self, task_id: int) -> bool:
        """Cancela una tarea."""
        task = self.tasks.get(task_id)
        if task:
            task.stop()
            if task.chunk_manager:
                task.chunk_manager.cleanup_chunks()
            task.status = DownloadTask.STATUS_CANCELLED
            db.update_download(task_id, status=DownloadTask.STATUS_CANCELLED)
            return True
        return False
    
    def remove_task(self, task_id: int) -> bool:
        """Elimina una tarea."""
        if task_id in self.tasks:
            self.cancel_task(task_id)
            del self.tasks[task_id]
            db.delete_download(task_id)
            return True
        return False
    
    def get_task(self, task_id: int) -> Optional[DownloadTask]:
        """Obtiene una tarea."""
        return self.tasks.get(task_id)


downloader = Downloader()
