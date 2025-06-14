# utils/file_utils.py
"""
Fonctions utilitaires pour la gestion des fichiers
"""

import mimetypes
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from .constants import ERROR_MESSAGES, LIMITS


def sanitize_filename(filename: str) -> str:
    """Nettoie un nom de fichier pour le rendre sûr"""
    # Remplacer les caractères interdits
    forbidden_chars = '<>:"/\\|?*'
    for char in forbidden_chars:
        filename = filename.replace(char, '_')
    
    # Supprimer les caractères de contrôle
    filename = ''.join(char for char in filename if ord(char) >= 32)
    
    # Gérer l'extension
    if '.' in filename:
        name, ext = filename.rsplit('.', 1)
        # Limiter la longueur du nom
        if len(name) > 200:
            name = name[:200]
        filename = f"{name}.{ext}"
    else:
        # Pas d'extension
        if len(filename) > 200:
            filename = filename[:200]
    
    # Éviter les noms réservés Windows
    reserved_names = [
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    ]
    
    name_without_ext = filename.split('.')[0].upper()
    if name_without_ext in reserved_names:
        filename = f"_{filename}"

    return filename


def clean_filename(filename: str) -> str:
    """Alias de :func:`sanitize_filename` pour compatibilité."""
    return sanitize_filename(filename)


@dataclass
class EmailConfig:
    """Configuration d'un email"""
    to: List[str]
    subject: str
    body: str
    cc: List[str] = field(default_factory=list)
    bcc: List[str] = field(default_factory=list)
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    priority: str = "normal"

    def add_attachment(self, filename: str, data: bytes, mimetype: str):
        """Ajoute une pièce jointe"""
        self.attachments.append({
            'filename': filename,
            'data': data,
            'mimetype': mimetype,
        })


ATTACHMENT_MIME_TYPES = {
    'pdf': 'application/pdf',
    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'txt': 'text/plain',
    'html': 'text/html',
    'json': 'application/json',
    'csv': 'text/csv',
    'zip': 'application/zip',
}


def format_file_size(size_bytes: int) -> str:
    """Formate une taille de fichier en unité lisible"""
    if size_bytes < 0:
        return "Taille invalide"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    size = float(size_bytes)
    unit_index = 0
    
    while size >= 1024.0 and unit_index < len(units) - 1:
        size /= 1024.0
        unit_index += 1
    
    # Format selon la taille
    if unit_index == 0:  # Bytes
        return f"{int(size)} {units[unit_index]}"
    elif size >= 100:  # Pas de décimales si >= 100
        return f"{int(size)} {units[unit_index]}"
    elif size >= 10:  # Une décimale si >= 10
        return f"{size:.1f} {units[unit_index]}"
    else:  # Deux décimales si < 10
        return f"{size:.2f} {units[unit_index]}"


def get_file_icon(filename: str) -> str:
    """Retourne l'icône appropriée selon l'extension du fichier"""
    ext = filename.lower().split('.')[-1] if '.' in filename else ''
    
    icons = {
        # Documents
        'pdf': '📄',
        'doc': '📝',
        'docx': '📝',
        'odt': '📝',
        'rtf': '📝',
        'txt': '📃',
        
        # Tableurs
        'xlsx': '📊',
        'xls': '📊',
        'csv': '📊',
        'ods': '📊',
        
        # Présentations
        'pptx': '📽️',
        'ppt': '📽️',
        'odp': '📽️',
        
        # Images
        'png': '🖼️',
        'jpg': '🖼️',
        'jpeg': '🖼️',
        'gif': '🖼️',
        'bmp': '🖼️',
        'svg': '🖼️',
        'webp': '🖼️',
        
        # Archives
        'zip': '📦',
        'rar': '📦',
        '7z': '📦',
        'tar': '📦',
        'gz': '📦',
        
        # Audio
        'mp3': '🎵',
        'wav': '🎵',
        'ogg': '🎵',
        'flac': '🎵',
        
        # Vidéo
        'mp4': '🎬',
        'avi': '🎬',
        'mkv': '🎬',
        'mov': '🎬',
        
        # Code
        'py': '🐍',
        'js': '💻',
        'html': '🌐',
        'css': '🎨',
        'json': '📋',
        'xml': '📋',
        
        # Autres
        'eml': '📧',
        'msg': '📧'
    }
    
    return icons.get(ext, '📎')


def get_file_extension(filename: str) -> str:
    """Extrait l'extension d'un fichier"""
    if '.' in filename:
        return filename.rsplit('.', 1)[1].lower()
    return ''


def is_valid_filename(filename: str) -> bool:
    """Vérifie si un nom de fichier est valide"""
    if not filename or filename.strip() == '':
        return False
    
    # Vérifier les caractères interdits
    forbidden_chars = '<>:"|?*'
    if any(char in filename for char in forbidden_chars):
        return False
    
    # Vérifier la longueur (255 caractères max sur la plupart des systèmes)
    if len(filename) > 255:
        return False
    
    # Vérifier les noms réservés Windows
    reserved_names = [
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    ]
    
    name_without_ext = filename.split('.')[0].upper()
    if name_without_ext in reserved_names:
        return False
    
    return True


def get_mime_type(filename: str) -> str:
    """Détermine le type MIME d'un fichier"""
    mime_type, _ = mimetypes.guess_type(filename)
    
    if mime_type:
        return mime_type
    
    # Types personnalisés pour certaines extensions
    custom_types = {
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'msg': 'application/vnd.ms-outlook',
        'eml': 'message/rfc822'
    }
    
    ext = get_file_extension(filename)
    return custom_types.get(ext, 'application/octet-stream')


def is_text_file(filename: str) -> bool:
    """Vérifie si un fichier est un fichier texte"""
    text_extensions = {
        'txt', 'md', 'csv', 'log', 'json', 'xml', 'html', 'htm',
        'css', 'js', 'py', 'java', 'c', 'cpp', 'h', 'hpp',
        'yaml', 'yml', 'ini', 'cfg', 'conf', 'sh', 'bat'
    }
    
    ext = get_file_extension(filename)
    return ext in text_extensions


def is_document_file(filename: str) -> bool:
    """Vérifie si un fichier est un document"""
    doc_extensions = {
        'pdf', 'doc', 'docx', 'odt', 'rtf', 'txt',
        'xls', 'xlsx', 'ods', 'csv',
        'ppt', 'pptx', 'odp'
    }
    
    ext = get_file_extension(filename)
    return ext in doc_extensions


def is_image_file(filename: str) -> bool:
    """Vérifie si un fichier est une image"""
    image_extensions = {
        'jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg',
        'webp', 'ico', 'tiff', 'tif'
    }
    
    ext = get_file_extension(filename)
    return ext in image_extensions


def create_unique_filename(base_name: str, existing_names: List[str]) -> str:
    """Crée un nom de fichier unique en ajoutant un suffixe si nécessaire"""
    if base_name not in existing_names:
        return base_name
    
    # Séparer le nom et l'extension
    if '.' in base_name:
        name, ext = base_name.rsplit('.', 1)
        ext = f".{ext}"
    else:
        name = base_name
        ext = ""
    
    # Essayer avec des suffixes numériques
    counter = 1
    while True:
        new_name = f"{name}_{counter}{ext}"
        if new_name not in existing_names:
            return new_name
        counter += 1


def organize_files_by_type(files: List[str]) -> Dict[str, List[str]]:
    """Organise une liste de fichiers par type"""
    organized = {
        'documents': [],
        'images': [],
        'archives': [],
        'audio': [],
        'video': [],
        'code': [],
        'autres': []
    }
    
    type_mapping = {
        'documents': ['pdf', 'doc', 'docx', 'odt', 'rtf', 'txt', 'xls', 'xlsx', 'ods', 'csv', 'ppt', 'pptx', 'odp'],
        'images': ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp', 'ico', 'tiff', 'tif'],
        'archives': ['zip', 'rar', '7z', 'tar', 'gz', 'bz2'],
        'audio': ['mp3', 'wav', 'ogg', 'flac', 'aac', 'wma', 'm4a'],
        'video': ['mp4', 'avi', 'mkv', 'mov', 'wmv', 'flv', 'webm'],
        'code': ['py', 'js', 'html', 'css', 'java', 'cpp', 'c', 'h', 'json', 'xml', 'yaml', 'yml']
    }
    
    # Inverser le mapping pour une recherche plus efficace
    ext_to_type = {}
    for file_type, extensions in type_mapping.items():
        for ext in extensions:
            ext_to_type[ext] = file_type
    
    for file in files:
        ext = get_file_extension(file)
        file_type = ext_to_type.get(ext, 'autres')
        organized[file_type].append(file)
    
    return organized


def get_file_info(filepath: str) -> Dict[str, Any]:
    """Récupère les informations d'un fichier"""
    info = {
        'name': os.path.basename(filepath),
        'extension': get_file_extension(filepath),
        'exists': os.path.exists(filepath),
        'is_file': os.path.isfile(filepath) if os.path.exists(filepath) else False,
        'is_directory': os.path.isdir(filepath) if os.path.exists(filepath) else False
    }
    
    if info['exists'] and info['is_file']:
        stat = os.stat(filepath)
        info.update({
            'size': stat.st_size,
            'size_formatted': format_file_size(stat.st_size),
            'created': datetime.fromtimestamp(stat.st_ctime),
            'modified': datetime.fromtimestamp(stat.st_mtime),
            'mime_type': get_mime_type(filepath)
        })
    
    return info


def split_path(filepath: str) -> Dict[str, str]:
    """Divise un chemin en ses composants"""
    directory = os.path.dirname(filepath)
    filename = os.path.basename(filepath)
    
    name = filename
    extension = ''
    
    if '.' in filename:
        name, extension = filename.rsplit('.', 1)
    
    return {
        'directory': directory,
        'filename': filename,
        'name': name,
        'extension': extension,
        'full_path': filepath
    }


def is_valid_email(email: str) -> bool:
    """Vérifie si une adresse email est valide"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_uploaded_file(file, max_size_mb: int = LIMITS.get('max_file_size_mb', 50)) -> (bool, str):
    """Valide un fichier uploadé.

    Args:
        file: Objet fichier (par ex. Streamlit UploadedFile).
        max_size_mb: Taille maximale autorisée en mégaoctets.

    Returns:
        Tuple (is_valid, message). ``message`` est ``None`` si le fichier est valide.
    """
    if not file:
        return False, "Aucun fichier fourni"

    size = getattr(file, "size", None)
    try:
        if size is None:
            data = file.getvalue()
            size = len(data) if data else 0
    except Exception:
        size = 0

    if size == 0:
        return False, "Le fichier est vide"

    if size > max_size_mb * 1024 * 1024:
        return False, ERROR_MESSAGES['file_too_large'].format(limit=max_size_mb)

    filename = getattr(file, "name", "")
    if not is_text_file(filename):
        return False, ERROR_MESSAGES['invalid_format']

    try:
        content = file.getvalue()
        if isinstance(content, bytes):
            content.decode('utf-8')
        else:
            str(content)
    except Exception:
        return False, "Le fichier semble corrompu ou illisible"

    return True, None
