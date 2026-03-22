import eel
import os
import threading
import time
from pathlib import Path
from ..core.downloader import downloader, DownloadTask
from ..core.database import db
from ..core.config import load_config, save_config as persist_config
from ..core.social_downloader import (
    is_social_media_url,
    SocialMediaDownloader,
    QUALITY_OPTIONS,
    FORMAT_OPTIONS,
)
from ..utils.helpers import get_file_extension, get_file_icon, check_ffmpeg

# Initialize Eel with the web assets directory
web_dir = os.path.join(os.path.dirname(__file__), "web")
eel.init(web_dir)

# --- Python exposed to JS ---


@eel.expose
def add_download(url, quality="best", file_format=None):
    task = downloader.create_task(url, quality=quality, file_format=file_format)
    if task:
        # Run download in a separate thread
        thread = threading.Thread(target=downloader.start_download, args=(task.id,))
        thread.daemon = True
        thread.start()
        return True
    return False


@eel.expose
def check_url_type(url):
    return is_social_media_url(url)


@eel.expose
def get_quality_options():
    return QUALITY_OPTIONS


@eel.expose
def get_format_options():
    return FORMAT_OPTIONS


@eel.expose
def get_available_formats(url):
    return SocialMediaDownloader.get_available_formats(url)


@eel.expose
def pause_task(task_id):
    return downloader.pause_task(task_id)


@eel.expose
def resume_task(task_id):
    return downloader.resume_task(task_id)


@eel.expose
def cancel_task(task_id):
    return downloader.cancel_task(task_id)


@eel.expose
def remove_task(task_id):
    return downloader.remove_task(task_id)


@eel.expose
def get_config():
    return load_config()


@eel.expose
def get_stats():
    return db.get_statistics()


@eel.expose
def get_all_downloads():
    stats = db.get_statistics()
    history = db.get_all_downloads()
    active = db.get_active_downloads()
    return {"stats": stats, "history": history, "active": active}


@eel.expose
def save_settings(new_config):
    current = load_config()
    allowed_keys = [
        'default_threads', 'default_download_path', 'max_speed_kbps',
        'checksum_type', 'timeout', 'minimize_to_tray',
    ]
    filtered_config = {k: v for k, v in new_config.items() if k in allowed_keys}
    current.update(filtered_config)
    persist_config(current)
    return True


@eel.expose
def browse_folder():
    try:
        from tkinter import filedialog, Tk

        root = Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        folder = filedialog.askdirectory()
        root.destroy()
        return folder if folder else None
    except:
        return None


@eel.expose
def open_download(download_id):
    entry = db.get_download(download_id)
    if not entry:
        return False

    filename = entry.get("filename")
    destination = entry.get("destination", "")

    if not filename or filename == "pending":
        return False

    full_path = os.path.join(destination, filename)

    if not os.path.exists(full_path):
        return False

    try:
        import subprocess
        import sys

        if sys.platform == "darwin":
            subprocess.run(["open", full_path])
        elif sys.platform == "win32":
            os.startfile(full_path)
        else:
            subprocess.run(["xdg-open", full_path])
        return True
    except Exception as e:
        print(f"Error opening file: {e}")
        return False


@eel.expose
def get_history(status=None):
    if status == 'all':
        status = None
    items = db.get_all_downloads(status)
    return {"history": items}


@eel.expose
def clear_history(status=None):
    count = db.clear_history(status)
    return count


@eel.expose
def check_engine_status():
    return {
        "ffmpeg": check_ffmpeg(),
        "ytdlp": True
    }


@eel.expose
def delete_download(download_id):
    return db.delete_download(download_id)


@eel.expose
def add_download_with_options(
    url, quality="best", file_format=None, destination=None, max_speed_kbps=0, title=None, thumbnail=None
):
    # Handle multiple URLs (Batch)
    urls = [u.strip() for u in url.split("\n") if u.strip()]
    if not urls:
        return False
    
    success_count = 0
    for single_url in urls:
        if not destination:
            destination = load_config()["default_download_path"]
        
        # For batch, if we have multiple URLs, title/thumb might only apply to the first one 
        # unless they were fetched before. But usually batch is just raw URLs.
        current_title = title if len(urls) == 1 else None
        current_thumb = thumbnail if len(urls) == 1 else None

        task = downloader.create_task(
            single_url,
            destination=destination,
            quality=quality,
            file_format=file_format,
            max_speed_kbps=max_speed_kbps,
            title=current_title,
            thumbnail=current_thumb,
        )
        if task:
            thread = threading.Thread(target=downloader.start_download, args=(task.id,))
            thread.daemon = True
            thread.start()
            success_count += 1
    
    return success_count > 0


@eel.expose
def set_download_path(path):
    config = load_config()
    config["default_download_path"] = path
    persist_config(config)
    return True


@eel.expose
def get_download_path():
    return load_config()["default_download_path"]

@eel.expose
def get_legal_notice():
    notice_path = os.path.join(os.path.dirname(__file__), "web", "LEGAL_NOTICE.md")
    if os.path.exists(notice_path):
        with open(notice_path, "r") as f:
            return f.read()
    return "Aviso Legal no encontrado."


@eel.expose
def get_local_ip():
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"


# --- Background Update Loop ---


def update_loop():
    while True:
        try:
            # Prepare task data for JSON serialization
            serialized_tasks = {}
            for task_id, task in downloader.tasks.items():
                serialized_tasks[task_id] = {
                    "id": task.id,
                    "url": task.url,
                    "status": task.status,
                    "progress": task.progress,
                    "total_size": task.total_size,
                    "downloaded_size": task.downloaded_size,
                    "speed": task.speed,
                    "title": task.title,
                    "thumbnail": task.thumbnail,
                    "filename": str(task.output_file.name) if task.output_file else task.title or "Descarga",
                }

            stats = db.get_statistics()
            # Add current throughput to stats
            current_speed = sum(
                t.speed for t in downloader.tasks.values() if t.status == "DOWNLOADING"
            )
            stats["total_speed"] = current_speed

            eel.update_tasks(serialized_tasks, stats)

        except Exception as e:
            print(f"Update loop error: {e}")

        eel.sleep(1.0)


def run_gui():
    thread = threading.Thread(target=update_loop)
    thread.daemon = True
    thread.start()

    # host="127.0.0.1" restricts access to localhost only (security: prevents LAN exposure)
    try:
        print(f"App server running on http://{get_local_ip()}:8000")
        eel.start("index.html", size=(1280, 800), host="127.0.0.1", port=8000)
    except (SystemExit, KeyboardInterrupt):
        pass


if __name__ == "__main__":
    run_gui()
