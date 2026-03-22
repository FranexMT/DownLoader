import os
import shutil
import re
import time
import threading
import logging
from pathlib import Path
from typing import Optional, Callable, Dict, Any

import yt_dlp

from .database import db
from .config import load_config
from ..utils.validators import sanitize_filename

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SOCIAL_MEDIA_DOMAINS = [
    r"(?:www\.)?youtube\.com",
    r"(?:www\.)?youtu\.be",
    r"(?:www\.)?instagram\.com",
    r"(?:www\.)?twitter\.com",
    r"(?:www\.)?x\.com",
    r"(?:www\.)?facebook\.com",
    r"(?:www\.)?fb\.watch",
    r"(?:www\.)?tiktok\.com",
    r"(?:www\.)?reddit\.com",
    r"(?:www\.)?vimeo\.com",
    r"(?:www\.)?twitch\.tv",
    r"(?:www\.)?soundcloud\.com",
    r"(?:www\.)?spotify\.com",
    r"(?:www\.)?dailymotion\.com",
    r"(?:www\.)?coub\.com",
    r"(?:www\.)?pinterest\.com",
    r"(?:www\.)?linkedin\.com",
    r"(?:www\.)?tumblr\.com",
    r"(?:www\.)?imgur\.com",
    r"(?:www\.)?bilibili\.com",
    r"(?:www\.)?weibo\.com",
]

SUPPORTED_PATTERNS = [
    re.compile(domain, re.IGNORECASE) for domain in SOCIAL_MEDIA_DOMAINS
]


def is_social_media_url(url: str) -> bool:
    """
    Check if a URL belongs to a supported social media platform.

    Args:
        url: The URL to check.

    Returns:
        True if the URL is from a supported platform, False otherwise.
    """
    if not url:
        return False

    for pattern in SUPPORTED_PATTERNS:
        if pattern.search(url):
            return True

    return False


QUALITY_OPTIONS = [
    {"id": "best", "label": "Best Quality", "format": "bestvideo+bestaudio/best"},
    {
        "id": "1080p",
        "label": "1080p",
        "format": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
    },
    {
        "id": "720p",
        "label": "720p",
        "format": "bestvideo[height<=720]+bestaudio/best[height<=720]",
    },
    {
        "id": "480p",
        "label": "480p",
        "format": "bestvideo[height<=480]+bestaudio/best[height<=480]",
    },
    {"id": "audio_only", "label": "Audio Only (MP3)", "format": "bestaudio/best"},
    {"id": "video_only", "label": "Video Only", "format": "bestvideo/best"},
]

FORMAT_OPTIONS = [
    {"id": "mp4", "label": "MP4", "ext": "mp4"},
    {"id": "webm", "label": "WebM", "ext": "webm"},
    {"id": "mkv", "label": "MKV", "ext": "mkv"},
    {"id": "mp3", "label": "MP3", "ext": "mp3"},
    {"id": "m4a", "label": "M4A (Audio)", "ext": "m4a"},
    {"id": "flac", "label": "FLAC (Audio)", "ext": "flac"},
]


class SocialMediaDownloader:
    """
    Downloader for social media content using yt-dlp.

    Supports pause, resume, and cancel operations for downloads from
    various social media platforms.
    """

    STATUS_PENDING = "PENDING"
    STATUS_DOWNLOADING = "DOWNLOADING"
    STATUS_PAUSED = "PAUSED"
    STATUS_COMPLETED = "COMPLETED"
    STATUS_FAILED = "FAILED"
    STATUS_CANCELLED = "CANCELLED"

    def __init__(
        self,
        task_id: int,
        url: str,
        destination: str,
        quality: str = "best",
        file_format: str = None,
    ):
        """
        Initialize the social media downloader.

        Args:
            task_id: The unique identifier for this download task.
            url: The URL of the media to download.
            destination: The directory where the file will be saved.
            quality: Quality preset (best, 1080p, 720p, 480p, audio_only, video_only)
            file_format: Preferred format (mp4, webm, mkv, mp3, m4a, flac)
        """
        self.task_id = task_id
        self.url = url
        self.destination = Path(destination)
        self.destination.mkdir(parents=True, exist_ok=True)
        self.quality = quality
        self.file_format = file_format

        self.status = self.STATUS_PENDING
        self.progress = 0.0
        self.total_size = 0
        self.downloaded_size = 0
        self.speed = 0.0
        self.filename = None
        self.error = None

        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()

        self._progress_callback: Optional[Callable] = None
        self._ydl_opts = None
        self._download_info: Dict[str, Any] = {}

    def set_progress_callback(self, callback: Callable[[float, float], None]) -> None:
        """
        Set the callback function for progress updates.

        Args:
            callback: A function that takes progress (0-100) and speed (bytes/sec).
        """
        self._progress_callback = callback

    def _create_ydl_opts(self) -> Dict[str, Any]:
        """
        Create yt-dlp options dictionary with progress hooks.

        Returns:
            Dictionary of yt-dlp options.
        """
        config = load_config()
        browser = config.get("cookies_browser", "firefox")
        naming_template = config.get("naming_template", "%(title)s.%(ext)s")
        auto_subs = config.get("auto_subtitles", False)
        embed_subs = config.get("embed_subtitles", True)

        format_str = self._get_format_string()

        postprocessors = []
        if auto_subs and embed_subs:
             postprocessors.append({
                 "key": "FFmpegEmbedSubtitle",
             })
             
        if self.file_format in ["mp3", "m4a", "flac"]:
            postprocessors.append(
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": self.file_format
                    if self.file_format != "m4a"
                    else "m4a",
                }
            )
            postprocessors.append(
                {
                    "key": "FFmpegMetadata",
                    "add_metadata": True,
                }
            )
            postprocessors.append(
                {
                    "key": "EmbedThumbnail",
                }
            )
            postprocessors.append(
                {
                    "key": "FFmpegConcat",
                    "only_multi_video": True,
                }
            )

        opts = {
            "outtmpl": str(self.destination / naming_template),
            "format": format_str,
            "writethumbnail": True,
            "writesubtitles": auto_subs,
            "allsubtitles": auto_subs,
            "noplaylist": False,
            "quiet": False,
            "no_warnings": False,
            "extract_flat": False,
            "ignoreerrors": True,
            "postprocessors": postprocessors if postprocessors else [],
        }

        if browser and browser != "none":
            opts["cookiefrombrowser"] = browser

        if self._stop_event is None:
            self._stop_event = threading.Event()

        stop_event = self._stop_event
        pause_event = self._pause_event

        def progress_hook(d: Dict[str, Any]) -> None:
            if stop_event.is_set():
                raise yt_dlp.utils.DownloadCancelled("Download stopped by user")

            pause_event.wait()

            if d["status"] == "downloading":
                total_bytes = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
                downloaded_bytes = d.get("downloaded_bytes", 0)

                if total_bytes > 0:
                    self.progress = (downloaded_bytes / total_bytes) * 100
                    self.total_size = total_bytes

                self.downloaded_size = downloaded_bytes

                speed = d.get("speed")
                if speed:
                    self.speed = speed

                db.update_download(
                    self.task_id,
                    downloaded_size=downloaded_bytes,
                    total_size=self.total_size,
                    speed=self.speed,
                )

                if self._progress_callback:
                    self._progress_callback(self.progress, self.speed)

            elif d["status"] == "finished":
                filename = d.get("filename")
                if filename:
                    self.filename = os.path.basename(filename)
                    self.progress = 100.0
                    logger.info(f"Download finished: {self.filename}")

            elif d["status"] == "error":
                self.error = d.get("error", "Unknown error")
                logger.error(f"Download error: {self.error}")

        opts["progress_hooks"] = [progress_hook]

        return opts

    def _get_format_string(self) -> str:
        """Get yt-dlp format string based on quality and format options."""
        quality_map = {
            "best": "bestvideo+bestaudio/best",
            "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
            "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
            "480p": "bestvideo[height<=480]+bestaudio/best[height<=480]",
            "audio_only": "bestaudio/best",
            "video_only": "bestvideo/best",
        }

        format_str = quality_map.get(self.quality, "bestvideo+bestaudio/best")

        if self.file_format and self.file_format != "mp4":
            ext_format_map = {
                "webm": re.sub(r'\bbest\b', "best[ext=webm]", format_str, count=1),
                "mkv": re.sub(r'\bbest\b', "best[ext=mkv]", format_str, count=1),
            }
            if self.file_format in ext_format_map:
                format_str = ext_format_map[self.file_format]

        return format_str

    @staticmethod
    def get_available_formats(url: str) -> Dict[str, Any]:
        """
        Get available formats for a URL (without downloading).

        Args:
            url: The URL to check.

        Returns:
            Dictionary with video info and available formats.
        """
        if not is_social_media_url(url):
            return {"error": "URL not supported", "formats": [], "info": {}}

        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
            "skip_download": True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                if not info:
                    return {
                        "error": "Could not extract info",
                        "formats": [],
                        "info": {},
                    }

                formats = []
                if "formats" in info:
                    for f in info["formats"]:
                        format_info = {
                            "format_id": f.get("format_id", ""),
                            "ext": f.get("ext", ""),
                            "resolution": f.get("resolution", "unknown"),
                            "filesize": f.get("filesize", 0),
                            "tbr": f.get("tbr", 0),
                            "vcodec": f.get("vcodec", "none"),
                            "acodec": f.get("acodec", "none"),
                            "format_note": f.get("format_note", ""),
                        }
                        if format_info["resolution"] and "x" in str(
                            format_info["resolution"]
                        ):
                            try:
                                height = int(format_info["resolution"].split("x")[1])
                                format_info["height"] = height
                            except:
                                pass
                        formats.append(format_info)

                return {
                    "error": None,
                    "info": {
                        "title": info.get("title", ""),
                        "thumbnail": info.get("thumbnail", ""),
                        "duration": info.get("duration", 0),
                        "uploader": info.get("uploader", ""),
                    },
                    "formats": formats,
                }
        except Exception as e:
            return {"error": str(e), "formats": [], "info": {}}

    def pause(self) -> None:
        """Pause the current download."""
        if self.status == self.STATUS_DOWNLOADING:
            self.status = self.STATUS_PAUSED
            self._pause_event.clear()
            db.update_download(self.task_id, status=self.STATUS_PAUSED)
            logger.info(f"Download {self.task_id} paused")

    def resume(self) -> None:
        """Resume a paused download."""
        if self.status == self.STATUS_PAUSED:
            self.status = self.STATUS_DOWNLOADING
            self._pause_event.set()
            db.update_download(self.task_id, status=self.STATUS_DOWNLOADING)
            logger.info(f"Download {self.task_id} resumed")

    def stop(self) -> None:
        """Stop the current download."""
        self._stop_event.set()
        self._pause_event.set()
        self.status = self.STATUS_CANCELLED
        db.update_download(self.task_id, status=self.STATUS_CANCELLED)
        logger.info(f"Download {self.task_id} stopped")

    def download(self) -> bool:
        """
        Start the download process.

        Returns:
            True if download completed successfully, False otherwise.
        """
        if not is_social_media_url(self.url):
            self.error = f"URL not supported: {self.url}"
            logger.error(self.error)
            db.update_download(
                self.task_id, status=self.STATUS_FAILED, error_message=self.error
            )
            return False

        try:
            self.status = self.STATUS_DOWNLOADING
            db.update_download(
                self.task_id,
                status=self.STATUS_DOWNLOADING,
                start_time=time.time(),
                destination=str(self.destination),
            )

            logger.info(f"Starting download for: {self.url}")

            self._ydl_opts = self._create_ydl_opts()

            with yt_dlp.YoutubeDL(self._ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=True)

                if info:
                    self._download_info = info
                    self.filename = ydl.prepare_filename(info)
                    self.filename = os.path.basename(self.filename)

                    full_path = self.destination / self.filename
                    if full_path.exists():
                        self.total_size = full_path.stat().st_size

                    db.update_download(
                        self.task_id,
                        filename=str(full_path),
                        total_size=self.total_size,
                        status=self.STATUS_COMPLETED,
                        end_time=time.time(),
                        title=info.get("title"),
                        thumbnail=info.get("thumbnail"),
                    )

                    self.status = self.STATUS_COMPLETED
                    self.progress = 100.0

                    logger.info(f"Download completed: {self.filename}")
                    return True
                else:
                    raise Exception("Failed to extract video information")

        except yt_dlp.utils.DownloadCancelled:
            self.status = self.STATUS_CANCELLED
            db.update_download(self.task_id, status=self.STATUS_CANCELLED)
            logger.info(f"Download {self.task_id} cancelled")
            return False

        except yt_dlp.utils.DownloadError as e:
            self.status = self.STATUS_FAILED
            self.error = str(e)
            logger.error(f"Download error for {self.task_id}: {e}")
            db.update_download(
                self.task_id, status=self.STATUS_FAILED, error_message=str(e)
            )
            return False

        except Exception as e:
            self.status = self.STATUS_FAILED
            self.error = str(e)
            logger.error(f"Unexpected error for {self.task_id}: {e}")
            db.update_download(
                self.task_id, status=self.STATUS_FAILED, error_message=str(e)
            )
            return False

        finally:
            self._cleanup()

    def _cleanup(self) -> None:
        """Limpia archivos temporales de la descarga."""
        try:
            # Buscar y eliminar archivos .part en el directorio de destino
            download_dir = Path(self.destination).parent
            for part_file in download_dir.glob("*.part"):
                part_file.unlink(missing_ok=True)

            # Buscar y eliminar directorios temporales de yt-dlp
            for tmp_dir in download_dir.glob(".tmp*"):
                if tmp_dir.is_dir():
                    shutil.rmtree(tmp_dir, ignore_errors=True)
        except Exception as e:
            logger.warning(f"Error limpiando archivos temporales: {e}")

    def get_info(self) -> Dict[str, Any]:
        """
        Get information about the downloaded media.

        Returns:
            Dictionary containing media information.
        """
        return {
            "title": self._download_info.get("title"),
            "uploader": self._download_info.get("uploader"),
            "upload_date": self._download_info.get("upload_date"),
            "duration": self._download_info.get("duration"),
            "view_count": self._download_info.get("view_count"),
            "like_count": self._download_info.get("like_count"),
            "description": self._download_info.get("description"),
            "tags": self._download_info.get("tags"),
            "filename": self.filename,
            "filesize": self.total_size,
        }
