#!/usr/bin/env python3
import argparse
import sys
import subprocess
import os
from colorama import init, Fore, Style
from ..core import downloader, load_config
from ..core.database import db
from ..utils.helpers import format_bytes, format_speed, open_file

init(autoreset=True)


def cmd_add(args):
    url = args.url
    destination = args.destination or load_config()["default_download_path"]
    quality = args.quality or "best"
    file_format = args.format or None
    max_speed = args.speed or 0

    task = downloader.create_task(
        url,
        destination,
        quality=quality,
        file_format=file_format,
        max_speed_kbps=max_speed,
    )
    if not task:
        print(f"{Fore.RED}✗ URL inválida{Style.RESET_ALL}")
        return

    print(f"{Fore.CYAN}Creando descarga #{task.id}{Style.RESET_ALL}")
    print(f"  URL: {url}")
    print(f"  Destino: {destination}")
    if task.is_social:
        print(f"  Calidad: {quality}")
        if file_format:
            print(f"  Formato: {file_format}")
    if max_speed > 0:
        print(f"  Velocidad máxima: {max_speed} KB/s")

    print(f"{Fore.YELLOW}Iniciando descarga...{Style.RESET_ALL}")
    success = downloader.start_download(task.id)

    if success:
        db_entry = db.get_download(task.id)
        filename = db_entry.get("filename", "Unknown") if db_entry else "Unknown"
        total_size = db_entry.get("total_size", 0) if db_entry else 0
        file_path = db_entry.get("destination", "") if db_entry else ""
        full_path = os.path.join(file_path, filename) if filename != "Unknown" else None
        checksum = db_entry.get("checksum", "") if db_entry else ""

        print(f"{Fore.GREEN}✓ Descarga completada{Style.RESET_ALL}")
        print(f"  Archivo: {filename}")
        print(f"  Tamaño: {format_bytes(total_size)}")
        if checksum:
            print(f"  Checksum: {checksum}")
        if full_path and os.path.exists(full_path):
            print(f"  Ubicación: {full_path}")
    else:
        print(f"{Fore.RED}✗ Error: {task.error}{Style.RESET_ALL}")


def cmd_list(args):
    tasks = downloader.tasks
    if not tasks:
        print(f"{Fore.YELLOW}No hay descargas activas.{Style.RESET_ALL}")
        return

    print(f"\n{Fore.CYAN}=== Descargas Activas ==={Style.RESET_ALL}\n")
    for task in tasks.values():
        status_colors = {
            "PENDING": Fore.WHITE,
            "DOWNLOADING": Fore.GREEN,
            "PAUSED": Fore.YELLOW,
            "COMPLETED": Fore.GREEN,
            "FAILED": Fore.RED,
            "CANCELLED": Fore.RED,
        }

        status_color = status_colors.get(task.status, Fore.WHITE)

        if task.status == "COMPLETED":
            print(f"#{task.id} | {status_color}{task.status} ✓{Style.RESET_ALL}")
            print(
                f"    Archivo: {task.output_file.name if task.output_file else 'N/A'}"
            )
            if task.total_size > 0:
                print(f"    Tamaño: {format_bytes(task.total_size)}")
        else:
            print(
                f"#{task.id} | {status_color}{task.status}{Style.RESET_ALL} | {task.url}"
            )
            if task.total_size > 0:
                progress = f"{task.progress:.1f}%"
                downloaded = format_bytes(task.downloaded_size)
                total = format_bytes(task.total_size)
                speed = format_speed(task.speed)
                print(
                    f"    Progreso: {downloaded} / {total} ({progress}) | Velocidad: {speed}"
                )
            elif task.status == "PENDING":
                print(f"    Estado: Esperando...")


def cmd_history(args):
    history = db.get_all_downloads()
    if not history:
        print(f"{Fore.YELLOW}No hay historial de descargas.{Style.RESET_ALL}")
        return

    print(f"\n{Fore.CYAN}=== Historial de Descargas ==={Style.RESET_ALL}\n")
    for entry in history:
        status_colors = {
            "COMPLETED": Fore.GREEN,
            "FAILED": Fore.RED,
            "CANCELLED": Fore.RED,
        }

        status_color = status_colors.get(entry.get("status", ""), Fore.WHITE)

        print(
            f"#{entry['id']} | {status_color}{entry.get('status', 'UNKNOWN')}{Style.RESET_ALL}"
        )
        print(f"    Archivo: {entry.get('filename', 'Unknown')}")
        print(f"    Tamaño: {format_bytes(entry.get('total_size', 0))}")
        print(f"    URL: {entry.get('url', '')}")
        print()


def cmd_pause(args):
    if downloader.pause_task(args.id):
        print(f"{Fore.YELLOW}Descarga #{args.id} pausada.{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}Descarga #{args.id} no encontrada.{Style.RESET_ALL}")


def cmd_resume(args):
    if downloader.resume_task(args.id):
        print(f"{Fore.GREEN}Descarga #{args.id} reanudada.{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}Descarga #{args.id} no encontrada.{Style.RESET_ALL}")


def cmd_cancel(args):
    if downloader.cancel_task(args.id):
        print(f"{Fore.RED}Descarga #{args.id} cancelada.{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}Descarga #{args.id} no encontrada.{Style.RESET_ALL}")


def cmd_remove(args):
    if downloader.remove_task(args.id):
        print(f"{Fore.YELLOW}Descarga #{args.id} eliminada.{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}Descarga #{args.id} no encontrada.{Style.RESET_ALL}")


def cmd_open(args):
    entry = db.get_download(args.id)
    if not entry:
        print(f"{Fore.RED}Descarga #{args.id} no encontrada.{Style.RESET_ALL}")
        return

    filename = entry.get("filename")
    destination = entry.get("destination", "")

    if not filename or filename == "pending":
        print(
            f"{Fore.YELLOW}La descarga #{args.id} no tiene archivo generado.{Style.RESET_ALL}"
        )
        return

    full_path = os.path.join(destination, filename)

    print(f"{Fore.CYAN}Abriendo: {full_path}{Style.RESET_ALL}")
    if not open_file(full_path):
        print(f"{Fore.RED}No se pudo abrir el archivo: {full_path}{Style.RESET_ALL}")


def cmd_clear(args):
    db.clear_history(args.status)
    print(f"{Fore.GREEN}Historial limpiado.{Style.RESET_ALL}")


def cmd_stats(args):
    stats = db.get_statistics()
    print(f"\n{Fore.CYAN}=== Estadísticas ==={Style.RESET_ALL}")
    print(f"Total: {stats['total']}")
    print(f"Completadas: {Fore.GREEN}{stats['completed']}{Style.RESET_ALL}")
    print(f"Fallidas: {Fore.RED}{stats['failed']}{Style.RESET_ALL}")
    print(f"Bytes totales: {format_bytes(stats['total_bytes'])}")


def cmd_dashboard(args):
    stats = db.get_statistics()
    history = db.get_all_downloads()
    active = db.get_active_downloads()

    print(
        f"\n{Fore.CYAN}╔══════════════════════════════════════════════════════════════╗{Style.RESET_ALL}"
    )
    print(
        f"{Fore.CYAN}║                    📥 DownLoader Dashboard                     ║{Style.RESET_ALL}"
    )
    print(
        f"{Fore.CYAN}╠══════════════════════════════════════════════════════════════╣{Style.RESET_ALL}"
    )
    print(
        f"{Fore.CYAN}║  Total: {stats['total']:<6}  | Completadas: {Fore.GREEN}{stats['completed']}{Fore.CYAN}  | Fallidas: {Fore.RED}{stats['failed']}{Fore.CYAN}  ║{Style.RESET_ALL}"
    )
    print(
        f"{Fore.CYAN}║  Descargado: {format_bytes(stats['total_bytes']):<40}         ║{Style.RESET_ALL}"
    )
    print(
        f"{Fore.CYAN}╠══════════════════════════════════════════════════════════════╣{Style.RESET_ALL}"
    )
    print(
        f"{Fore.CYAN}║  DESCARGAS ACTIVAS ({len(active):<3})                                           ║{Style.RESET_ALL}"
    )

    if active:
        for entry in active:
            status_color = (
                Fore.YELLOW if entry.get("status") == "PAUSED" else Fore.GREEN
            )
            filename = entry.get("filename", "Unknown")
            if len(filename) > 40:
                filename = filename[:37] + "..."
            progress = entry.get("downloaded_size", 0)
            total = entry.get("total_size", 0)
            pct = f"{(progress / total * 100):.1f}%" if total > 0 else "0%"
            print(
                f"{Fore.CYAN}║  #{entry['id']:<4} {status_color}{entry.get('status', ''):<12}{Fore.CYAN} {filename:<40} ║{Style.RESET_ALL}"
            )
            print(
                f"{Fore.CYAN}║        Progreso: {format_bytes(progress)} / {format_bytes(total):<10} ({pct}){' ' * 18}║{Style.RESET_ALL}"
            )
    else:
        print(f"{Fore.CYAN}║  Ninguna descarga activa{' ' * 40}║{Style.RESET_ALL}")

    print(
        f"{Fore.CYAN}╠══════════════════════════════════════════════════════════════╣{Style.RESET_ALL}"
    )
    print(f"{Fore.CYAN}║  ÚLTIMAS DESCARGAS{' ' * 45}║{Style.RESET_ALL}")

    recent = history[:10] if len(history) > 10 else history
    for entry in recent:
        status_colors = {
            "COMPLETED": Fore.GREEN,
            "FAILED": Fore.RED,
            "CANCELLED": Fore.RED,
        }
        status_color = status_colors.get(entry.get("status", ""), Fore.WHITE)
        filename = entry.get("filename", "Unknown")
        if len(filename) > 35:
            filename = filename[:32] + "..."
        size = format_bytes(entry.get("total_size", 0))
        print(
            f"{Fore.CYAN}║  #{entry['id']:<4} {status_color}{entry.get('status', ''):<12}{Fore.CYAN} {filename:<35} {size:<10}║{Style.RESET_ALL}"
        )

    print(
        f"{Fore.CYAN}╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}"
    )
    print()
    print("Comandos: open <id> | pause <id> | resume <id> | cancel <id> | remove <id>")


def cmd_config(args):
    from ..core.config import save_config

    config = load_config()
    if args.show:
        print(f"\n{Fore.CYAN}=== Configuración ==={Style.RESET_ALL}")
        print(f"Hilos por defecto: {config['default_threads']}")
        print(f"Ruta de descarga: {config['default_download_path']}")
        print(f"Timeout: {config['timeout']}s")
        print(f"Velocidad máxima: {config.get('max_speed_kbps', 0)} KB/s")
        print(f"Checksum: {config.get('checksum_type', 'Ninguna')}")
        print(f"Tema: {config['theme']}")
    else:
        changed = False
        if args.threads:
            config["default_threads"] = args.threads
            print(f"{Fore.GREEN}Hilos configurados: {args.threads}{Style.RESET_ALL}")
            changed = True
        if args.path:
            config["default_download_path"] = args.path
            print(f"{Fore.GREEN}Ruta de descarga: {args.path}{Style.RESET_ALL}")
            changed = True
        if args.speed is not None:
            config["max_speed_kbps"] = args.speed
            print(f"{Fore.GREEN}Velocidad máxima: {args.speed} KB/s{Style.RESET_ALL}")
            changed = True
        if args.checksum:
            if args.checksum == "none":
                config["checksum_type"] = None
                print(f"{Fore.GREEN}Checksum desactivado{Style.RESET_ALL}")
            else:
                config["checksum_type"] = args.checksum
                print(f"{Fore.GREEN}Checksum: {args.checksum}{Style.RESET_ALL}")
            changed = True

        if changed:
            save_config(config)
        else:
            print(f"{Fore.YELLOW}No se especificaron cambios{Style.RESET_ALL}")


def main():
    parser = argparse.ArgumentParser(
        prog="downloader", description="DownLoader V2.0 - Gestor de descargas"
    )
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponibles")

    parser_add = subparsers.add_parser("add", help="Agregar nueva descarga")
    parser_add.add_argument("url", help="URL del archivo")
    parser_add.add_argument("destination", nargs="?", help="Ruta de destino")
    parser_add.add_argument(
        "--quality",
        "-q",
        choices=["best", "1080p", "720p", "480p", "audio_only", "video_only"],
        help="Calidad de descarga (solo para redes sociales)",
    )
    parser_add.add_argument(
        "--format",
        "-f",
        choices=["mp4", "webm", "mkv", "mp3", "m4a", "flac"],
        help="Formato de archivo",
    )
    parser_add.add_argument(
        "--speed",
        "-s",
        type=int,
        default=0,
        help="Velocidad máxima en KB/s (0 = sin límite)",
    )

    subparsers.add_parser("list", help="Listar descargas activas")
    subparsers.add_parser("history", help="Ver historial")
    subparsers.add_parser("stats", help="Ver estadísticas")
    subparsers.add_parser("dashboard", help="Panel de control")

    parser_pause = subparsers.add_parser("pause", help="Pausar descarga")
    parser_pause.add_argument("id", type=int, help="ID de la descarga")

    parser_resume = subparsers.add_parser("resume", help="Reanudar descarga")
    parser_resume.add_argument("id", type=int, help="ID de la descarga")

    parser_cancel = subparsers.add_parser("cancel", help="Cancelar descarga")
    parser_cancel.add_argument("id", type=int, help="ID de la descarga")

    parser_remove = subparsers.add_parser("remove", help="Eliminar descarga")
    parser_remove.add_argument("id", type=int, help="ID de la descarga")

    parser_open = subparsers.add_parser("open", help="Abrir archivo descargado")
    parser_open.add_argument("id", type=int, help="ID de la descarga")

    parser_clear = subparsers.add_parser("clear", help="Limpiar historial")
    parser_clear.add_argument("status", nargs="?", help="Limpiar por estado")

    parser_config = subparsers.add_parser("config", help="Configuración")
    parser_config.add_argument(
        "--show", action="store_true", help="Mostrar configuración"
    )
    parser_config.add_argument("--threads", type=int, help="Número de hilos")
    parser_config.add_argument("--path", type=str, help="Ruta de descarga")
    parser_config.add_argument("--speed", type=int, help="Velocidad máxima KB/s")
    parser_config.add_argument(
        "--checksum",
        choices=["none", "md5", "sha256"],
        help="Tipo de verificación de integridad",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    commands = {
        "add": cmd_add,
        "list": cmd_list,
        "history": cmd_history,
        "stats": cmd_stats,
        "dashboard": cmd_dashboard,
        "pause": cmd_pause,
        "resume": cmd_resume,
        "cancel": cmd_cancel,
        "remove": cmd_remove,
        "open": cmd_open,
        "clear": cmd_clear,
        "config": cmd_config,
    }

    commands.get(args.command, lambda _: parser.print_help())(args)


if __name__ == "__main__":
    main()
