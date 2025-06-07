# managers/azure_blob_manager.py
"""Gestionnaire pour Azure Blob Storage avec navigation complète"""

import os
import io
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Vérifier la disponibilité d'Azure
try:
    from azure.storage.blob import BlobServiceClient
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False
    logger.warning("Modules Azure non disponibles")

# Import conditionnel pour docx
try:
    from docx import Document as DocxDocument
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    logger.warning("Module python-docx non disponible")

from models.dataclasses import Document


class AzureBlobManager:
    """Gestionnaire pour Azure Blob Storage avec navigation dans les dossiers"""
    
    def __init__(self):
        self.blob_service_client = None
        self.container_client = None
        try:
            self._init_blob_client()
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation d'AzureBlobManager : {e}")
            self.blob_service_client = None
    
    def _init_blob_client(self):
        """Initialise le client Azure Blob"""
        try:
            # Nettoyer l'environnement pour Hugging Face
            self._clean_env_for_azure()
            
            connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
            if connection_string and AZURE_AVAILABLE:
                self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
                logger.info("Client Azure Blob Storage initialisé avec succès")
            else:
                if not connection_string:
                    logger.warning("AZURE_STORAGE_CONNECTION_STRING non définie")
                if not AZURE_AVAILABLE:
                    logger.warning("Modules Azure non disponibles")
        except Exception as e:
            logger.error(f"Erreur initialisation Azure Blob : {e}")
            self.blob_service_client = None
    
    def _clean_env_for_azure(self):
        """Nettoie l'environnement pour Azure sur Hugging Face Spaces"""
        proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 
                      'NO_PROXY', 'no_proxy', 'REQUESTS_CA_BUNDLE', 'CURL_CA_BUNDLE']
        
        for var in proxy_vars:
            if var in os.environ:
                del os.environ[var]
        
        os.environ['CURL_CA_BUNDLE'] = ""
        os.environ['REQUESTS_CA_BUNDLE'] = ""
    
    def is_connected(self) -> bool:
        """Vérifie si la connexion est établie"""
        return self.blob_service_client is not None
    
    def list_containers(self) -> List[str]:
        """Liste tous les containers disponibles"""
        if not self.blob_service_client:
            return []
        
        try:
            containers = self.blob_service_client.list_containers()
            container_list = [container.name for container in containers]
            logger.info(f"Containers trouvés: {container_list}")
            return container_list
        except Exception as e:
            logger.error(f"Erreur listing containers : {e}")
            return []
    
    def list_folders(self, container_name: str, prefix: str = "") -> List[Dict[str, Any]]:
        """Liste les dossiers et fichiers dans un chemin donné"""
        if not self.blob_service_client:
            return []
        
        try:
            container_client = self.blob_service_client.get_container_client(container_name)
            
            folders = set()
            files = []
            
            blobs = container_client.list_blobs(name_starts_with=prefix)
            
            for blob in blobs:
                relative_path = blob.name[len(prefix):] if prefix else blob.name
                parts = relative_path.split('/')
                
                if len(parts) > 1 and parts[0]:
                    folders.add(parts[0])
                elif len(parts) == 1 and parts[0]:
                    files.append({
                        'name': parts[0],
                        'size': blob.size,
                        'last_modified': blob.last_modified,
                        'content_type': blob.content_settings.content_type if blob.content_settings else None,
                        'full_path': blob.name
                    })
            
            result = []
            
            for folder in sorted(folders):
                result.append({
                    'name': folder,
                    'type': 'folder',
                    'path': f"{prefix}{folder}/" if prefix else f"{folder}/"
                })
            
            for file in sorted(files, key=lambda x: x['name']):
                result.append({
                    'name': file['name'],
                    'type': 'file',
                    'size': file['size'],
                    'last_modified': file['last_modified'],
                    'content_type': file['content_type'],
                    'full_path': file['full_path']
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur listing dossiers : {e}")
            return []
    
    def download_file(self, container_name: str, blob_name: str) -> Optional[bytes]:
        """Télécharge un fichier depuis Azure Blob"""
        if not self.blob_service_client:
            return None
        
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=container_name,
                blob=blob_name
            )
            
            return blob_client.download_blob().readall()
            
        except Exception as e:
            logger.error(f"Erreur téléchargement blob : {e}")
            return None
    
    def extract_text_from_blob(self, container_name: str, blob_name: str) -> Optional[str]:
        """Extrait le texte d'un blob"""
        content_bytes = self.download_file(container_name, blob_name)
        
        if not content_bytes:
            return None
        
        file_ext = os.path.splitext(blob_name)[1].lower()
        
        try:
            if file_ext == '.txt':
                return content_bytes.decode('utf-8', errors='ignore')
            elif file_ext in ['.docx', '.doc'] and DOCX_AVAILABLE:
                doc = DocxDocument(io.BytesIO(content_bytes))
                return '\n'.join([paragraph.text for paragraph in doc.paragraphs])
            else:
                return f"[Format {file_ext} non supporté pour l'extraction de texte]"
        except Exception as e:
            logger.error(f"Erreur extraction texte : {e}")
            return None
    
    def get_all_files_in_folder(self, container_name: str, folder_path: str) -> List[Dict[str, Any]]:
        """Récupère récursivement tous les fichiers d'un dossier"""
        if not self.blob_service_client:
            return []
        
        try:
            container_client = self.blob_service_client.get_container_client(container_name)
            all_files = []
            
            blobs = container_client.list_blobs(name_starts_with=folder_path)
            
            for blob in blobs:
                if not blob.name.endswith('/'):
                    all_files.append({
                        'name': os.path.basename(blob.name),
                        'full_path': blob.name,
                        'size': blob.size,
                        'last_modified': blob.last_modified,
                        'folder': os.path.dirname(blob.name)
                    })
            
            return all_files
            
        except Exception as e:
            logger.error(f"Erreur récupération fichiers du dossier : {e}")
            return []