import os
import shutil
import time
import threading
import requests
import logging
import hashlib
import sys
import subprocess
from pathlib import Path
from typing import Optional, Callable
from .config import load_config
from .chunk_manager import ChunkManager
from .database import db
from .social_downloader import is_social_media_url, SocialMediaDownloader
from ..utils.validators import (
    is_valid_url,
    extract_filename_from_url,
    sanitize_filename,
)
from ..utils.helpers import send_notification

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def auto_update_ytdlp():
    """Actualiza yt-dlp automáticamente para asegurar que las descargas funcionen."""
    try:
        logger.info("Verificando actualizaciones del motor de descarga...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-U", "yt-dlp"], 
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        logger.info("Motor de descarga actualizado correctamente.")
    except Exception as e:
        logger.warning(f"No se pudo actualizar yt-dlp: {e}. Se usará la versión instalada.")


class DownloadTask:
    """Representa una tarea de descarga."""

    STATUS_PENDING = "PENDING"
    STATUS_DOWNLOADING = "DOWNLOADING"
    STATUS_PAUSED = "PAUSED"
    STATUS_COMPLETED = "COMPLETED"
    STATUS_FAILED = "FAILED"
    STATUS_CANCELLED = "CANCELLED"
    STATUS_VERIFYING = "VERIFYING"

    def __init__(
        self,
        task_id: int,
        url: str,
        destination: Path,
        num_threads: int = None,
        is_social: bool = False,
        quality: str = "best",
        file_format: str = None,
        max_speed_kbps: int = 0,
        title: str = None,
        thumbnail: str = None,
    ):
        self.id = task_id
        self.url = url
        self.destination = destination
        self.title = title
        self.thumbnail = thumbnail
        config = load_config()
        self.num_threads = num_threads or config["default_threads"]
        self.is_social = is_social
        self.quality = quality
        self.file_format = file_format
        self.max_speed_kbps = max_speed_kbps or config.get("max_speed_kbps", 0)

        self.status: str = self.STATUS_PENDING
        self.progress: float = 0.0
        self.total_size: int = 0
        self.downloaded_size: int = 0
        self.speed: float = 0.0
        self.error: Optional[str] = None
        self.checksum: Optional[str] = None
        self.checksum_type: Optional[str] = None
        self.verification_status: Optional[str] = None

        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()

        self.chunk_manager: Optional[ChunkManager] = None
        self.output_file: Optional[Path] = None
        self.social_downloader: Optional[SocialMediaDownloader] = None

    def stop(self):
        """Detiene la descarga."""
        self._stop_event.set()
        self._pause_event.set()

    def pause(self):
        """Pausa la descarga."""
        if self.status == self.STATUS_DOWNLOADING:
            self.status = self.STATUS_PAUSED
            self._pause_event.clear()
            self._save_progress()
            db.update_download(
                self.id, status=self.STATUS_PAUSED, downloaded_size=self.downloaded_size
            )

    def resume(self):
        """Reanuda la descarga."""
        if self.status == self.STATUS_PAUSED:
            self.status = self.STATUS_DOWNLOADING
            self._pause_event.set()
            db.update_download(self.id, status=self.STATUS_DOWNLOADING)

    def _save_progress(self):
        """Guarda el progreso actual para permitir resume real."""
        if self.chunk_manager:
            self.chunk_manager.save_state(self.downloaded_size, self.total_size)


class Downloader:
    """Motor de descargas con soporte para multithreading y pause/resume."""

    def __init__(self):
        self.config = load_config()
        self.tasks = {}
        self.task_lock = threading.Lock()
        self._callbacks = {}
        
        # Cleanup orphaned temp files on startup
        ChunkManager.global_cleanup(self.config["default_download_path"])
        
        # Auto-update downloader engine
        update_thread = threading.Thread(target=auto_update_ytdlp, daemon=True)
        update_thread.start()

        # Start scheduler thread
        threading.Thread(target=self._scheduler_loop, daemon=True).start()

    def _scheduler_loop(self):
        """Revisa cada minuto si hay descargas programadas."""
        while True:
            try:
                config = load_config()
                if config.get("scheduler_enabled"):
                    now = time.strftime("%H:%M")
                    target = config.get("scheduler_time", "02:00")
                    if now == target:
                        logger.info("Scheduler triggered. Starting pending downloads...")
                        pending = db.get_active_downloads() # Actually we want PENDING across all
                        # Simple logic: trigger the UI or just start them here
                        # For simplicity, we'll just start anything that's PENDING
                        all_downloads = db.get_all_downloads()
                        for item in all_downloads:
                            if item["status"] == "PENDING":
                                self.start_download(item["id"])
                        time.sleep(61) # Avoid double triggering in the same minute
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
            time.sleep(30)

    def set_progress_callback(self, task_id: int, callback: Callable):
        """Establece callback para progreso."""
        self._callbacks[task_id] = callback

    def _throttle(self, task: DownloadTask, chunk_size: int):
        """Aplica limitación de velocidad si está configurada."""
        if task.max_speed_kbps <= 0:
            return

        target_bytes_per_sec = task.max_speed_kbps * 1024
        expected_time = chunk_size / target_bytes_per_sec
        time.sleep(expected_time)

    def create_task(
        self,
        url: str,
        destination: str = None,
        quality: str = "best",
        file_format: str = None,
        max_speed_kbps: int = 0,
        title: str = None,
        thumbnail: str = None,
    ) -> Optional[DownloadTask]:
        """Crea una nueva tarea de descarga."""
        if not is_valid_url(url):
            logger.error(f"URL inválida: {url}")
            return None

        destination = destination or self.config["default_download_path"]
        dest_path = Path(destination)
        dest_path.mkdir(parents=True, exist_ok=True)

        is_social = is_social_media_url(url)

        with self.task_lock:
            task_id = db.create_download(url, "pending", str(dest_path), title=title, thumbnail=thumbnail)
            task = DownloadTask(
                task_id,
                url,
                dest_path,
                self.config["default_threads"],
                is_social=is_social,
                quality=quality,
                file_format=file_format,
                max_speed_kbps=max_speed_kbps or self.config.get("max_speed_kbps", 0),
                title=title,
                thumbnail=thumbnail,
            )
            self.tasks[task_id] = task

        return task

    def start_download(self, task_id: int) -> bool:
        """Inicia la descarga."""
        task = self.tasks.get(task_id)
        if not task:
            return False

        if task.is_social:
            return self.start_social_download(task_id)

        try:
            # Verificar espacio en disco
            total, used, free = shutil.disk_usage(task.destination)
            
            task.status = DownloadTask.STATUS_DOWNLOADING
            db.update_download(
                task_id, status=DownloadTask.STATUS_DOWNLOADING, start_time=time.time()
            )

            with requests.head(
                task.url, allow_redirects=True, timeout=self.config["timeout"]
            ) as response:
                task.total_size = int(response.headers.get("content-length", 0))
                
                # Si conocemos el tamaño, verificar que quepa en el disco
                if task.total_size > 0 and free < (task.total_size + 1024 * 1024 * 50): # 50MB extra de margen
                    raise Exception(f"Espacio insuficiente en disco. Se requieren {task.total_size / 1024 / 1024:.1f} MB.")
                
                accept_ranges = response.headers.get("accept-ranges", "none")

                supports_resume = accept_ranges.lower() == "bytes"

                filename = extract_filename_from_url(task.url, dict(response.headers))
                task.output_file = task.destination / sanitize_filename(filename)

                db.update_download(
                    task_id, filename=str(task.output_file), total_size=task.total_size
                )

            if task.total_size == 0:
                task.status = DownloadTask.STATUS_FAILED
                task.error = "No se pudo obtener el tamaño del archivo"
                db.update_download(
                    task_id, status=task.STATUS_FAILED, error_message=task.error
                )
                return False

            if task.total_size < 1024 * 1024 * 10 or task.num_threads == 1:
                self._download_single(task)
            else:
                self._download_multithread(task, supports_resume)

            if task.status == DownloadTask.STATUS_DOWNLOADING:
                self._verify_and_complete(task)

            return task.status == DownloadTask.STATUS_COMPLETED

        except Exception as e:
            task.status = DownloadTask.STATUS_FAILED
            task.error = str(e)
            logger.error(f"Error en descarga {task_id}: {e}")
            db.update_download(task_id, status=task.STATUS_FAILED, error_message=str(e))
            send_notification(
                "Error en Descarga", 
                f"La descarga {task_id} ha fallado: {str(e)}"
            )
            return False

    def _verify_and_complete(self, task: DownloadTask):
        """Verifica checksum y marca como completada."""
        task.status = DownloadTask.STATUS_VERIFYING
        task.progress = 100.0

        checksum_type = self.config.get("checksum_type", None)
        if checksum_type and task.output_file and task.output_file.exists():
            task.verification_status = "Verificando..."
            db.update_download(task.id, status=task.STATUS_VERIFYING)

            file_checksum = self._calculate_checksum(
                str(task.output_file), checksum_type
            )
            task.checksum = file_checksum
            task.checksum_type = checksum_type

            if task.id in self._callbacks:
                self._callbacks[task.id](
                    task.progress, task.speed, "checksum", file_checksum
                )

            db.update_download(task.id, checksum=file_checksum)
            task.verification_status = "Verificado"

        task.status = DownloadTask.STATUS_COMPLETED
        db.update_download(
            task.id,
            status=DownloadTask.STATUS_COMPLETED,
            downloaded_size=task.total_size,
            end_time=time.time(),
        )
        send_notification(
            "Descarga Completada", 
            f"El archivo {task.output_file.name} se ha descargado correctamente."
        )

    def _calculate_checksum(self, filepath: str, algorithm: str = "sha256") -> str:
        """Calcula el checksum de un archivo."""
        if not os.path.exists(filepath):
            return ""
        hash_func = hashlib.new(algorithm)
        try:
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hash_func.update(chunk)
            return hash_func.hexdigest()
        except Exception as e:
            logger.error(f"Error calculando checksum: {e}")
            return ""

    def _download_single(self, task: DownloadTask):
        """Descarga con un solo hilo con soporte para pause/resume real y throttling."""
        try:
            task.chunk_manager = ChunkManager(str(task.output_file))
            chunk_path = task.chunk_manager.get_chunk_path(0)

            resume_state = task.chunk_manager.load_state()
            downloaded = 0
            mode = "wb"
            headers = {}

            if resume_state and resume_state.get("downloaded_size", 0) > 0:
                downloaded = resume_state["downloaded_size"]
                if downloaded >= task.total_size:
                    logger.info(f"Descarga ya completada para {task.id}")
                    task.downloaded_size = downloaded
                    task.progress = 100.0
                    return
                headers["Range"] = f"bytes={downloaded}-"
                mode = "ab"
                logger.info(f"Reanudando descarga desde {downloaded} bytes")
            else:
                task.chunk_manager.create_temp_dir()

            task.chunk_manager.create_temp_dir()
            start_time = time.time() - (
                resume_state.get("elapsed", 0) if resume_state else 0
            )

            with requests.get(
                task.url, stream=True, headers=headers, timeout=self.config["timeout"]
            ) as response:
                response.raise_for_status()

                if response.status_code == 206:
                    content_range = response.headers.get("Content-Range", "")
                    if "bytes" in content_range:
                        start_byte = int(content_range.split("-")[0].split()[-1])
                        if start_byte != downloaded:
                            logger.warning(
                                "El servidor no respeta Range header, reiniciando"
                            )
                            downloaded = 0
                            mode = "wb"

                chunk_num = 0
                if downloaded > 0:
                    chunk_num = 1

                with open(chunk_path, mode) as f:
                    if mode == "rb+":
                        f.seek(0, 2)
                        downloaded = f.tell()
                        f.seek(downloaded)

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

                            self._throttle(task, len(chunk))

                            if downloaded % (1024 * 1024) < 8192:
                                task.chunk_manager.save_state(
                                    downloaded, task.total_size, elapsed
                                )

                            db.update_download(
                                task.id, downloaded_size=downloaded, speed=task.speed
                            )

                            if task.id in self._callbacks:
                                self._callbacks[task.id](task.progress, task.speed)

            if task.status == DownloadTask.STATUS_DOWNLOADING:
                task.chunk_manager.merge_chunks(1)

        except Exception as e:
            task.error = str(e)
            task.status = DownloadTask.STATUS_FAILED
            db.update_download(task.id, status=task.STATUS_FAILED, error_message=str(e))

    def _download_multithread(self, task: DownloadTask, supports_resume: bool):
        """Descarga con múltiples hilos con soporte para throttling."""
        chunk_size = task.total_size // task.num_threads
        ranges = []

        for i in range(task.num_threads):
            start = i * chunk_size
            end = (
                start + chunk_size - 1
                if i < task.num_threads - 1
                else task.total_size - 1
            )
            ranges.append((start, end))

        task.chunk_manager = ChunkManager(str(task.output_file))

        if supports_resume:
            resume_info = task.chunk_manager.resume_info()
            if resume_info.get("resumable"):
                logger.info(
                    f"Reanudando descarga con {resume_info['chunks_downloaded']} chunks"
                )
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

            headers = {"Range": f"bytes={start}-{end}"}
            chunk_path = task.chunk_manager.get_chunk_path(thread_id)

            existing_size = 0
            if chunk_path.exists():
                existing_size = chunk_path.stat().st_size
                if existing_size >= (end - start + 1):
                    with lock:
                        downloaded_bytes[thread_id] = existing_size
                    return
                headers["Range"] = f"bytes={start + existing_size}-{end}"

            try:
                response = requests.get(
                    task.url,
                    headers=headers,
                    stream=True,
                    timeout=self.config["timeout"],
                )
                response.raise_for_status()

                mode = "ab" if existing_size > 0 else "wb"
                with open(chunk_path, mode) as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if task._stop_event.is_set():
                            break

                        task._pause_event.wait()

                        if chunk:
                            self._throttle(task, len(chunk))

                            f.write(chunk)
                            with lock:
                                downloaded_bytes[thread_id] += len(chunk)
                                task.downloaded_size = sum(downloaded_bytes)
                                task.progress = (
                                    task.downloaded_size / task.total_size
                                ) * 100

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

            db.update_download(
                task.id, downloaded_size=task.downloaded_size, speed=task.speed
            )

        for t in threads:
            t.join()

        if (
            task.status != DownloadTask.STATUS_CANCELLED
            and task.status != DownloadTask.STATUS_FAILED
        ):
            task.chunk_manager.merge_chunks(task.num_threads)

    def start_social_download(self, task_id: int) -> bool:
        """Inicia una descarga de redes sociales."""
        task = self.tasks.get(task_id)
        if not task:
            return False

        try:
            social_dl = SocialMediaDownloader(
                task_id,
                task.url,
                str(task.destination),
                quality=task.quality,
                file_format=task.file_format,
            )
            task.social_downloader = social_dl

            if task_id in self._callbacks:
                social_dl.set_progress_callback(self._callbacks[task_id])

            def run_download():
                result = social_dl.download()
                if result:
                    info = social_dl.get_info()
                    task.status = DownloadTask.STATUS_COMPLETED
                    task.progress = 100.0
                    task.title = info.get("title")
                    task.thumbnail = info.get("thumbnail")
                    if info.get("filename"):
                        task.output_file = task.destination / info.get("filename")
                    
                    db.update_download(
                        task.id,
                        status=DownloadTask.STATUS_COMPLETED,
                        title=task.title,
                        thumbnail=task.thumbnail,
                        filename=str(task.output_file) if task.output_file else None
                    )
                    
                    send_notification(
                        "Descarga Social Completada", 
                        f"El video se ha descargado correctamente."
                    )
                else:
                    task.status = task.STATUS_FAILED
                    send_notification(
                        "Error en Descarga Social", 
                        f"Hubo un error procesando el enlace de red social."
                    )

            thread = threading.Thread(target=run_download)
            thread.start()
            return True

        except Exception as e:
            task.status = DownloadTask.STATUS_FAILED
            task.error = str(e)
            logger.error(f"Error en descarga social {task_id}: {e}")
            db.update_download(
                task_id, status=DownloadTask.STATUS_FAILED, error_message=str(e)
            )
            return False

    def pause_task(self, task_id: int) -> bool:
        """Pausa una tarea."""
        task = self.tasks.get(task_id)
        if task:
            if task.is_social and task.social_downloader:
                task.social_downloader.pause()
            else:
                task.pause()
            return True
        return False

    def resume_task(self, task_id: int) -> bool:
        """Reanuda una tarea."""
        task = self.tasks.get(task_id)
        if task:
            if task.is_social and task.social_downloader:
                task.social_downloader.resume()
            else:
                task.resume()
                thread = threading.Thread(target=self.start_download, args=(task_id,))
                thread.start()
            return True
        return False

    def cancel_task(self, task_id: int) -> bool:
        """Cancela una tarea."""
        task = self.tasks.get(task_id)
        if task:
            if task.is_social and task.social_downloader:
                task.social_downloader.stop()
            else:
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
