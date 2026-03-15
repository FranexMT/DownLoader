#!/usr/bin/env python3
import argparse
import sys
from colorama import init, Fore, Style
from ..core import downloader, load_config
from ..core.database import db
from ..utils.helpers import format_bytes, format_speed

init(autoreset=True)


def cmd_add(args):
    url = args.url
    destination = args.destination or load_config()["default_download_path"]
    
    task = downloader.create_task(url, destination)
    if not task:
        print(f"{Fore.RED}✗ URL inválida{Style.RESET_ALL}")
        return
    
    print(f"{Fore.CYAN}Creando descarga #{task.id}{Style.RESET_ALL}")
    print(f"  URL: {url}")
    print(f"  Destino: {destination}")
    
    print(f"{Fore.YELLOW}Iniciando descarga...{Style.RESET_ALL}")
    success = downloader.start_download(task.id)
    
    if success:
        print(f"{Fore.GREEN}✓ Descarga completada{Style.RESET_ALL}")
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
            "CANCELLED": Fore.RED
        }
        
        status_color = status_colors.get(task.status, Fore.WHITE)
        
        print(f"#{task.id} | {status_color}{task.status}{Style.RESET_ALL} | {task.url}")
        if task.total_size > 0:
            progress = f"{task.progress:.1f}%"
            downloaded = format_bytes(task.downloaded_size)
            total = format_bytes(task.total_size)
            speed = format_speed(task.speed)
            print(f"    Progreso: {downloaded} / {total} ({progress}) | Velocidad: {speed}")


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
            "CANCELLED": Fore.RED
        }
        
        status_color = status_colors.get(entry.get('status', ''), Fore.WHITE)
        
        print(f"#{entry['id']} | {status_color}{entry.get('status', 'UNKNOWN')}{Style.RESET_ALL}")
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


def cmd_clear(args):
    db.clear_history(args.status)
    print(f"{Fore.GREEN}Historial limpiado.{Style.RESET_ALL}")


def cmd_stats(args):
    stats = db.get_statistics()
    print(f"\n{Fore.CYAN}=== Estadísticas ==={Style.RESET_ALL}")
    print(f"Total: {stats['total']}")
    print(f"Completadas: {Fore.GREEN}{stats['completed']}{Style.RESET_ALL}")
    print(f"Fallidas: {Fore.RED}{stats['failed']}{Style.RESET_ALL}")
    print(f"Bytes totals: {format_bytes(stats['total_bytes'])}")


def cmd_config(args):
    config = load_config()
    if args.show:
        print(f"\n{Fore.CYAN}=== Configuración ==={Style.RESET_ALL}")
        print(f"Hilos por defecto: {config['default_threads']}")
        print(f"Ruta de descarga: {config['default_download_path']}")
        print(f"Timeout: {config['timeout']}s")
        print(f"Tema: {config['theme']}")
    elif args.threads:
        config['default_threads'] = args.threads
        from ..core.config import save_config
        save_config(config)
        print(f"{Fore.GREEN}Hilos configurados: {args.threads}{Style.RESET_ALL}")
    elif args.path:
        config['default_download_path'] = args.path
        from ..core.config import save_config
        save_config(config)
        print(f"{Fore.GREEN}Ruta de descarga: {args.path}{Style.RESET_ALL}")


def main():
    parser = argparse.ArgumentParser(prog='downloader', description='DownLoader V2.0 - Gestor de descargas')
    subparsers = parser.add_subparsers(dest='command', help='Comandos disponibles')
    
    parser_add = subparsers.add_parser('add', help='Agregar nueva descarga')
    parser_add.add_argument('url', help='URL del archivo')
    parser_add.add_argument('destination', nargs='?', help='Ruta de destino')
    
    subparsers.add_parser('list', help='Listar descargas activas')
    subparsers.add_parser('history', help='Ver historial')
    subparsers.add_parser('stats', help='Ver estadísticas')
    
    parser_pause = subparsers.add_parser('pause', help='Pausar descarga')
    parser_pause.add_argument('id', type=int, help='ID de la descarga')
    
    parser_resume = subparsers.add_parser('resume', help='Reanudar descarga')
    parser_resume.add_argument('id', type=int, help='ID de la descarga')
    
    parser_cancel = subparsers.add_parser('cancel', help='Cancelar descarga')
    parser_cancel.add_argument('id', type=int, help='ID de la descarga')
    
    parser_remove = subparsers.add_parser('remove', help='Eliminar descarga')
    parser_remove.add_argument('id', type=int, help='ID de la descarga')
    
    parser_clear = subparsers.add_parser('clear', help='Limpiar historial')
    parser_clear.add_argument('status', nargs='?', help='Limpiar por estado')
    
    parser_config = subparsers.add_parser('config', help='Configuración')
    parser_config.add_argument('--show', action='store_true', help='Mostrar configuración')
    parser_config.add_argument('--threads', type=int, help='Número de hilos')
    parser_config.add_argument('--path', type=str, help='Ruta de descarga')

    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    commands = {
        'add': cmd_add,
        'list': cmd_list,
        'history': cmd_history,
        'stats': cmd_stats,
        'pause': cmd_pause,
        'resume': cmd_resume,
        'cancel': cmd_cancel,
        'remove': cmd_remove,
        'clear': cmd_clear,
        'config': cmd_config
    }
    
    commands.get(args.command, lambda _: parser.print_help())(args)


if __name__ == '__main__':
    main()
