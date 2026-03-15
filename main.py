#!/usr/bin/env python3
import sys
import argparse

def main():
    parser = argparse.ArgumentParser(description='DownLoader V2.0 - Gestor de Descargas')
    parser.add_argument('--gui', action='store_true', help='Iniciar interfaz gráfica')
    parser.add_argument('command', nargs='*', help='Comando CLI')
    
    args = parser.parse_args()
    
    if args.gui:
        from src.gui import run_gui
        run_gui()
    elif args.command:
        from src.cli import main as cli_main
        sys.argv = [sys.argv[0]] + args.command
        cli_main()
    else:
        print("⬇ DownLoader V2.0")
        print("\nUso:")
        print("  python main.py --gui              # Iniciar GUI")
        print("  python main.py add <url>          # CLI: agregar descarga")
        print("  python main.py history            # CLI: ver historial")
        print("  python main.py stats              # CLI: estadísticas")
        print("\nComandos CLI disponibles:")
        print("  add <url> [dest]     - Agregar descarga")
        print("  list                 - Listar descargas activas")
        print("  history              - Ver historial")
        print("  stats                - Estadísticas")
        print("  pause <id>           - Pausar descarga")
        print("  resume <id>          - Reanudar descarga")
        print("  cancel <id>          - Cancelar descarga")
        print("  remove <id>          - Eliminar descarga")
        print("  clear [status]       - Limpiar historial")
        print("  config --show        - Ver configuración")
        print("  config --threads N   - Configurar hilos")

if __name__ == '__main__':
    main()
