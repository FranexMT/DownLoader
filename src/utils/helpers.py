from datetime import datetime


def format_bytes(size: int) -> str:
    """Formatea bytes a formato legible."""
    if size <= 0:
        return "0 B"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    unit_index = 0
    size_float = float(size)
    
    while size_float >= 1024.0 and unit_index < len(units) - 1:
        size_float /= 1024.0
        unit_index += 1
    
    if unit_index == 0:
        return f"{int(size_float)} {units[unit_index]}"
    return f"{size_float:.2f} {units[unit_index]}"


def calculate_eta(downloaded: int, total: int, speed: float) -> str:
    """Calcula el tiempo restante estimado."""
    if speed <= 0 or downloaded >= total:
        return "--:--"
    
    remaining = total - downloaded
    seconds = remaining / speed
    
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}:{secs:02d}"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def format_speed(bytes_per_second: float) -> str:
    """Formatea la velocidad de descarga."""
    if bytes_per_second <= 0:
        return "0 B/s"
    return f"{format_bytes(int(bytes_per_second))}/s"


def format_timestamp(timestamp: float) -> str:
    """Formatea timestamp a fecha legible."""
    dt = datetime.fromtimestamp(timestamp)
    return dt.strftime("%Y-%m-%d %H:%M:%s")


def get_file_extension(filename: str) -> str:
    """Obtiene la extensión del archivo."""
    if '.' in filename:
        return filename.rsplit('.', 1)[1].lower()
    return ""


def get_file_icon(extension: str) -> str:
    """Retorna un icono según el tipo de archivo."""
    icons = {
        'zip': '📦',
        'rar': '📦',
        '7z': '📦',
        'tar': '📦',
        'gz': '📦',
        'mp3': '🎵',
        'wav': '🎵',
        'flac': '🎵',
        'mp4': '🎬',
        'avi': '🎬',
        'mkv': '🎬',
        'mov': '🎬',
        'jpg': '🖼️',
        'jpeg': '🖼️',
        'png': '🖼️',
        'gif': '🖼️',
        'svg': '🖼️',
        'pdf': '📕',
        'doc': '📄',
        'docx': '📄',
        'txt': '📝',
        'xls': '📊',
        'xlsx': '📊',
        'exe': '⚙️',
        'msi': '⚙️',
        'apk': '📱',
        'deb': '📦',
        'rpm': '📦',
        'iso': '💿',
    }
    return icons.get(extension.lower(), '📁')
