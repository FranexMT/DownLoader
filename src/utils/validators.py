import re
import hashlib
from urllib.parse import urlparse


def is_valid_url(url: str) -> bool:
    """Valida que la URL sea correcta."""
    if not url or not isinstance(url, str):
        return False
    
    try:
        result = urlparse(url)
        return all([result.scheme in ['http', 'https'], result.netloc])
    except Exception:
        return False


def extract_filename_from_url(url: str, headers: dict = None) -> str:
    """Extrae el nombre del archivo de la URL o headers."""
    if headers and 'content-disposition' in headers:
        content_disp = headers['content-disposition']
        match = re.search(r'filename[^;=\n]*=(([\'"]).*?\2|[^;\n]*)', content_disp)
        if match:
            filename = match.group(1).strip('"\'')
            if filename:
                return sanitize_filename(filename)
    
    parsed = urlparse(url)
    path = parsed.path
    
    if '/' in path:
        filename = path.rsplit('/', 1)[1]
        if filename:
            return sanitize_filename(filename)
    
    return "download"


def sanitize_filename(filename: str) -> str:
    """Limpia el nombre del archivo de caracteres inválidos."""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    filename = filename.strip('. ')
    
    if not filename:
        filename = "download"
    
    if len(filename) > 200:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:200 - len(ext) - 1] + '.' + ext if ext else name[:200]
    
    return filename


def verify_checksum(filepath: str, expected_hash: str, algorithm: str = 'sha256') -> bool:
    """Verifica el checksum del archivo descargado."""
    if not expected_hash:
        return True
    
    hash_func = getattr(hashlib, algorithm, None)
    if not hash_func:
        return True
    
    try:
        with open(filepath, 'rb') as f:
            while chunk := f.read(8192):
                hash_func.update(chunk)
        
        actual_hash = hash_func.hexdigest().lower()
        return actual_hash == expected_hash.lower()
    except Exception:
        return True


def get_file_hash(filepath: str, algorithm: str = 'sha256') -> str:
    """Calcula el hash de un archivo."""
    hash_func = getattr(hashlib, algorithm)()
    
    try:
        with open(filepath, 'rb') as f:
            while chunk := f.read(8192):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except Exception:
        return ""


def is_supported_url(url: str) -> bool:
    """Verifica si la URL es de un protocolo soportado."""
    if not url:
        return False
    
    parsed = urlparse(url)
    return parsed.scheme in ['http', 'https']
