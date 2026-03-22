import customtkinter as ctk
from tkinter import filedialog
import threading
import time
from pathlib import Path
from ..core import downloader, load_config
from ..core.database import db
from ..utils.helpers import (
    format_bytes,
    format_speed,
    get_file_icon,
    get_file_extension,
)
from ..utils.validators import extract_filename_from_url
from .system_tray import SystemTray

import logging

logger = logging.getLogger(__name__)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class DownloadCard(ctk.CTkFrame):
    """Tarjeta individual para una descarga."""

    def __init__(self, parent, task, update_callback=None, **kwargs):
        super().__init__(parent, **kwargs)

        self.task = task
        self.update_callback = update_callback
        self.last_progress = -1
        self.setup_ui()

    def setup_ui(self):
        ext = get_file_extension(self.task.output_file or "file")
        icon = get_file_icon(ext)

        self.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self, text=icon, font=("Segoe UI", 28)).grid(
            row=0, column=0, rowspan=2, padx=15, pady=10, sticky="ns"
        )

        self.name_label = ctk.CTkLabel(
            self,
            text=extract_filename_from_url(self.task.url)[:45] if self.task.url else "...",
            font=("Segoe UI", 13, "bold"),
            anchor="w",
        )
        self.name_label.grid(row=0, column=1, padx=10, pady=(10, 2), sticky="ew")

        self.status_label = ctk.CTkLabel(
            self,
            text=self.get_status_text(),
            font=("Segoe UI", 11),
            text_color=self.get_status_color(),
            anchor="w",
        )
        self.status_label.grid(row=1, column=1, padx=10, pady=(0, 5), sticky="ew")

        self.progress = ctk.CTkProgressBar(self, height=10, progress_color="#00d9a5")
        self.progress.set(self.task.progress / 100)
        self.progress.grid(row=2, column=1, padx=10, pady=(5, 5), sticky="ew")

        self.info_label = ctk.CTkLabel(
            self,
            text=self.get_info_text(),
            font=("Segoe UI", 10),
            text_color="gray",
            anchor="w",
        )
        self.info_label.grid(row=3, column=1, padx=10, pady=(0, 10), sticky="ew")

        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.grid(row=0, column=2, rowspan=4, padx=10, pady=10, sticky="ns")

        self.update_buttons()

    def get_status_text(self):
        status_map = {
            "PENDING": "⏳ Pendiente",
            "DOWNLOADING": "⬇ Descargando",
            "PAUSED": "⏸ Pausado",
            "COMPLETED": "✓ Completado",
            "FAILED": "✗ Error",
            "CANCELLED": "✗ Cancelado",
        }
        return status_map.get(self.task.status, self.task.status)

    def get_status_color(self):
        colors = {
            "PENDING": "gray",
            "DOWNLOADING": "#00d9a5",
            "PAUSED": "#ffc107",
            "COMPLETED": "#00d9a5",
            "FAILED": "#ff4757",
            "CANCELLED": "#ff4757",
        }
        return colors.get(self.task.status, "gray")

    def get_info_text(self):
        downloaded = format_bytes(self.task.downloaded_size)
        total = format_bytes(self.task.total_size)
        speed = format_speed(self.task.speed)
        return f"{downloaded} / {total} | {speed}"

    def update_buttons(self):
        for widget in self.btn_frame.winfo_children():
            widget.destroy()

        if self.task.status == "DOWNLOADING":
            ctk.CTkButton(
                self.btn_frame,
                text="⏸",
                width=35,
                height=30,
                fg_color="#ffc107",
                hover_color="#e6ac00",
                text_color="black",
                command=lambda: downloader.pause_task(self.task.id),
            ).pack(pady=2)

            ctk.CTkButton(
                self.btn_frame,
                text="✗",
                width=35,
                height=30,
                fg_color="#ff4757",
                hover_color="#ff6b6b",
                command=lambda: downloader.cancel_task(self.task.id),
            ).pack(pady=2)

        elif self.task.status == "PAUSED":
            ctk.CTkButton(
                self.btn_frame,
                text="▶",
                width=35,
                height=30,
                fg_color="#00d9a5",
                hover_color="#00f5b8",
                text_color="black",
                command=lambda: downloader.resume_task(self.task.id),
            ).pack(pady=2)

            ctk.CTkButton(
                self.btn_frame,
                text="✗",
                width=35,
                height=30,
                fg_color="#ff4757",
                hover_color="#ff6b6b",
                command=lambda: downloader.cancel_task(self.task.id),
            ).pack(pady=2)

        elif self.task.status in ["COMPLETED", "FAILED", "CANCELLED"]:
            ctk.CTkButton(
                self.btn_frame,
                text="🗑",
                width=35,
                height=30,
                fg_color="#6b7280",
                hover_color="#4b5563",
                command=lambda: downloader.remove_task(self.task.id),
            ).pack(pady=2)

    def update(self):
        try:
            self.progress.set(self.task.progress / 100)
            self.status_label.configure(
                text=self.get_status_text(), text_color=self.get_status_color()
            )
            self.info_label.configure(text=self.get_info_text())
            self.update_buttons()
        except Exception as e:
            logger.error(f"Error updating card: {e}")


class DownloadManagerGUI:
    """Interfaz gráfica principal con CustomTkinter."""

    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("⬇ DownLoader V2.0")
        self.root.geometry("900x650")
        self.root.minsize(800, 550)

        self.config = load_config()
        self.download_cards = {}
        self.system_tray = None

        self.setup_ui()
        self.load_history()
        self.start_auto_refresh()
        self._setup_system_tray()

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

    def setup_ui(self):
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(1, weight=1)

        self.create_sidebar()
        self.create_header()
        self.create_main_area()

    def create_sidebar(self):
        sidebar = ctk.CTkFrame(self.root, width=200, corner_radius=0)
        sidebar.grid(row=0, column=0, rowspan=3, sticky="nsew")
        sidebar.grid_rowconfigure(10, weight=1)

        ctk.CTkLabel(
            sidebar,
            text="⬇ DownLoader",
            font=("Segoe UI", 20, "bold"),
            text_color="#e94560",
        ).grid(row=0, column=0, padx=20, pady=(20, 10))

        ctk.CTkLabel(
            sidebar, text="V2.0", font=("Segoe UI", 10), text_color="gray"
        ).grid(row=1, column=0, padx=20, pady=(0, 20))

        self.stats_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        self.stats_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        self.total_label = ctk.CTkLabel(
            self.stats_frame, text="Total: 0", font=("Segoe UI", 12)
        )
        self.total_label.pack()

        self.completed_label = ctk.CTkLabel(
            self.stats_frame,
            text="Completadas: 0",
            font=("Segoe UI", 12),
            text_color="#00d9a5",
        )
        self.completed_label.pack()

        self.failed_label = ctk.CTkLabel(
            self.stats_frame,
            text="Fallidas: 0",
            font=("Segoe UI", 12),
            text_color="#ff4757",
        )
        self.failed_label.pack()

        ctk.CTkButton(
            sidebar,
            text="⚙ Configuración",
            fg_color="#1f2937",
            hover_color="#374151",
            command=self.open_config,
        ).grid(row=11, column=0, padx=20, pady=10, sticky="ew")

    def create_header(self):
        header = ctk.CTkFrame(self.root, height=80)
        header.grid(row=0, column=1, sticky="ew", padx=20, pady=(20, 10))
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(header, text="Nueva Descarga", font=("Segoe UI", 14, "bold")).grid(
            row=0, column=0, columnspan=3, padx=10, pady=(5, 10), sticky="w"
        )

        ctk.CTkLabel(header, text="🌐 URL:").grid(row=1, column=0, padx=10, sticky="w")

        self.url_entry = ctk.CTkEntry(
            header, placeholder_text="https://ejemplo.com/archivo.zip", height=35
        )
        self.url_entry.grid(row=1, column=1, padx=5, sticky="ew")

        ctk.CTkButton(
            header,
            text="📁",
            width=40,
            height=35,
            fg_color="#1f2937",
            hover_color="#374151",
            command=self.browse_folder,
        ).grid(row=1, column=2, padx=(5, 10))

        self.dest_entry = ctk.CTkEntry(
            header, placeholder_text="Carpeta de destino", height=35
        )
        self.dest_entry.grid(
            row=2, column=0, columnspan=2, padx=10, pady=(5, 0), sticky="ew"
        )
        self.dest_entry.insert(0, self.config["default_download_path"])

        ctk.CTkButton(
            header,
            text="⬇ DESCARGAR",
            fg_color="#e94560",
            hover_color="#ff6b6b",
            height=40,
            font=("Segoe UI", 12, "bold"),
            command=self.add_download,
        ).grid(row=2, column=2, padx=5, pady=(5, 0), sticky="ew")

    def create_main_area(self):
        self.notebook = ctk.CTkTabview(self.root)
        self.notebook.grid(row=1, column=1, sticky="nsew", padx=20, pady=(0, 10))

        self.downloads_tab = self.notebook.add("⬇ Descargas")
        self.history_tab = self.notebook.add("📋 Historial")

        self.downloads_scroll = ctk.CTkScrollableFrame(
            self.downloads_tab, label_text="Descargas Activas"
        )
        self.downloads_scroll.pack(fill="both", expand=True, padx=10, pady=10)

        self.history_scroll = ctk.CTkScrollableFrame(
            self.history_tab, label_text="Historial"
        )
        self.history_scroll.pack(fill="both", expand=True, padx=10, pady=10)

    def browse_folder(self):
        folder = filedialog.askdirectory(initialdir=self.dest_entry.get())
        if folder:
            self.dest_entry.delete(0, "end")
            self.dest_entry.insert(0, folder)

    def add_download(self):
        url = self.url_entry.get().strip()
        if not url:
            return

        destination = self.dest_entry.get().strip()

        task = downloader.create_task(url, destination)
        if task:
            self.url_entry.delete(0, "end")
            thread = threading.Thread(target=self.run_download, args=(task.id,))
            thread.daemon = True
            thread.start()
            self.refresh_downloads()

    def run_download(self, task_id):
        downloader.start_download(task_id)

    def refresh_downloads(self):
        for widget in self.downloads_scroll.winfo_children():
            widget.destroy()

        active_tasks = downloader.tasks.values()

        for task in active_tasks:
            card = DownloadCard(self.downloads_scroll, task, fg_color="#1f2937")
            card.pack(fill="x", pady=5, padx=5)
            self.download_cards[task.id] = card

        self.load_history()
        self.update_stats()

    def load_history(self):
        for widget in self.history_scroll.winfo_children():
            widget.destroy()

        history = db.get_all_downloads()

        for item in history[:50]:
            card = self.create_history_card(item)
            card.pack(fill="x", pady=3, padx=5)

    def create_history_card(self, item):
        ext = get_file_extension(item.get("filename", ""))
        icon = get_file_icon(ext)

        status_colors = {
            "COMPLETED": "#00d9a5",
            "FAILED": "#ff4757",
            "CANCELLED": "#ff4757",
        }
        status_color = status_colors.get(item.get("status", ""), "gray")

        card = ctk.CTkFrame(self.history_scroll, fg_color="#1f2937")

        ctk.CTkLabel(card, text=icon, font=("Segoe UI", 18)).pack(
            side="left", padx=10, pady=10
        )

        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(
            info_frame,
            text=item.get("filename", "Unknown")[:50],
            font=("Segoe UI", 11, "bold"),
            anchor="w",
        ).pack(anchor="w", padx=5)

        size = format_bytes(item.get("total_size", 0))
        status = item.get("status", "UNKNOWN")

        ctk.CTkLabel(
            info_frame,
            text=f"{size} | {status}",
            font=("Segoe UI", 10),
            text_color=status_color,
            anchor="w",
        ).pack(anchor="w", padx=5)

        return card

    def update_stats(self):
        stats = db.get_statistics()
        self.total_label.configure(text=f"Total: {stats['total']}")
        self.completed_label.configure(text=f"Completadas: {stats['completed']}")
        self.failed_label.configure(text=f"Fallidas: {stats['failed']}")

    def start_auto_refresh(self):
        self.refresh_downloads()
        self.root.after(2000, self.start_auto_refresh)

    def open_config(self):
        config_win = ctk.CTkToplevel(self.root)
        config_win.title("⚙ Configuración")
        config_win.geometry("450x500")
        config_win.transient(self.root)

        frame = ctk.CTkFrame(config_win)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(frame, text="⚙ Configuración", font=("Segoe UI", 16, "bold")).pack(
            pady=(0, 20)
        )

        ctk.CTkLabel(frame, text="Hilos de descarga:").pack(anchor="w")
        threads_var = ctk.CTkSlider(frame, from_=1, to=16, number_of_steps=15)
        threads_var.set(self.config["default_threads"])
        threads_var.pack(fill="x", pady=(5, 15))

        ctk.CTkLabel(frame, text="Timeout (segundos):").pack(anchor="w")
        timeout_entry = ctk.CTkEntry(frame)
        timeout_entry.insert(0, str(self.config["timeout"]))
        timeout_entry.pack(fill="x", pady=(5, 15))

        ctk.CTkLabel(frame, text="Velocidad máxima (KB/s, 0 = sin límite):").pack(
            anchor="w"
        )
        speed_entry = ctk.CTkEntry(frame)
        speed_entry.insert(0, str(self.config.get("max_speed_kbps", 0)))
        speed_entry.pack(fill="x", pady=(5, 15))

        ctk.CTkLabel(frame, text="Verificación de integridad:").pack(anchor="w")
        checksum_var = ctk.CTkOptionMenu(
            frame,
            values=["Ninguna", "MD5", "SHA256"],
            fg_color="#1f2937",
            button_color="#1f2937",
        )
        current_checksum = self.config.get("checksum_type", None)
        if current_checksum == "md5":
            checksum_var.set("MD5")
        elif current_checksum == "sha256":
            checksum_var.set("SHA256")
        else:
            checksum_var.set("Ninguna")
        checksum_var.pack(fill="x", pady=(5, 15))

        minimize_var = ctk.CTkCheckBox(
            frame, text="Minimizar a bandeja al cerrar", onvalue=True, offvalue=False
        )
        if self.config.get("minimize_to_tray", True):
            minimize_var.select()
        else:
            minimize_var.deselect()
        minimize_var.pack(anchor="w", pady=(5, 15))

        def save():
            from ..core.config import save_config

            self.config["default_threads"] = int(threads_var.get())
            self.config["timeout"] = int(timeout_entry.get())
            self.config["max_speed_kbps"] = int(speed_entry.get())

            checksum_value = checksum_var.get()
            if checksum_value == "MD5":
                self.config["checksum_type"] = "md5"
            elif checksum_value == "SHA256":
                self.config["checksum_type"] = "sha256"
            else:
                self.config["checksum_type"] = None

            self.config["minimize_to_tray"] = minimize_var.get()
            save_config(self.config)
            config_win.destroy()

        ctk.CTkButton(
            frame,
            text="💾 GUARDAR",
            fg_color="#00d9a5",
            text_color="black",
            command=save,
        ).pack(pady=20, fill="x")

    def on_closing(self):
        if self.config.get("minimize_to_tray", True):
            self.root.withdraw()
        else:
            self.cleanup()
            self.root.destroy()

    def cleanup(self):
        """Limpia recursos al cerrar."""
        if self.system_tray:
            self.system_tray.stop()

    def _setup_system_tray(self):
        """Configura el system tray."""
        self.system_tray = SystemTray(self.root, downloader)
        self.system_tray.run()


def run_gui():
    app = DownloadManagerGUI()


if __name__ == "__main__":
    run_gui()
