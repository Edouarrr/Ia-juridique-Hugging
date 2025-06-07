# managers/azure_blob_manager.py
"""Gestionnaire Azure Blob Storage"""

import os
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
import streamlit as st

try:
    from azure.storage.blob import BlobServiceClient, ContainerClient
    from azure.core.exceptions import ResourceNotFoundError
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False

logger = logging.getLogger(__name__)

class AzureBlobManager:
    """Gère les opérations avec Azure Blob Storage"""
    
    def __init__(self):
        """Initialise le gestionnaire Azure Blob"""
        self.blob_service_client = None
        self.connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        
        if self.connection_string and AZURE_AVAILABLE:
            try:
                self.blob_service_client = BlobServiceClient.from_connection_string(
                    self.connection_string
                )
                logger.info("✅ Connexion Azure Blob Storage établie")
            except Exception as e:
                logger.error(f"❌ Erreur connexion Azure Blob: {e}")
                st.warning(f"Impossible de se connecter à Azure Blob Storage: {str(e)}")
        else:
            if not AZURE_AVAILABLE:
                logger.warning("⚠️ Azure SDK non installé")
            else:
                logger.warning("⚠️ AZURE_STORAGE_CONNECTION_STRING non configuré")
    
    def is_connected(self) -> bool:
        """Vérifie si la connexion est établie"""
        return self.blob_service_client is not None
    
    def list_containers(self) -> List[str]:
        """Liste tous les containers disponibles"""
        if not self.is_connected():
            return []
        
        try:
            containers = []
            for container in self.blob_service_client.list_containers():
                containers.append(container.name)
            return containers
        except Exception as e:
            logger.error(f"Erreur listing containers: {e}")
            return []
    
    def list_blobs(self, container_name: str, prefix: str = "") -> List[Dict[str, Any]]:
        """Liste les blobs dans un container avec un préfixe optionnel"""
        if not self.is_connected():
            return []
        
        try:
            container_client = self.blob_service_client.get_container_client(container_name)
            blobs = []
            
            for blob in container_client.list_blobs(name_starts_with=prefix):
                blobs.append({
                    'name': blob.name,
                    'size': blob.size,
                    'last_modified': blob.last_modified,
                    'content_type': blob.content_settings.content_type if blob.content_settings else None,
                    'metadata': blob.metadata
                })
            
            return blobs
        except ResourceNotFoundError:
            logger.error(f"Container '{container_name}' non trouvé")
            return []
        except Exception as e:
            logger.error(f"Erreur listing blobs: {e}")
            return []
    
    def list_folder_contents(self, container_name: str, folder_path: str = "") -> List[Dict[str, Any]]:
        """Liste le contenu d'un dossier (blobs et sous-dossiers)"""
        if not self.is_connected():
            return []
        
        try:
            container_client = self.blob_service_client.get_container_client(container_name)
            
            # Ajouter le slash si nécessaire
            prefix = folder_path
            if prefix and not prefix.endswith('/'):
                prefix += '/'
            
            items = []
            folders = set()
            
            # Lister tous les blobs avec le préfixe
            for blob in container_client.list_blobs(name_starts_with=prefix):
                # Enlever le préfixe pour obtenir le chemin relatif
                relative_path = blob.name[len(prefix):] if prefix else blob.name
                
                # Vérifier si c'est un sous-dossier
                if '/' in relative_path:
                    # C'est dans un sous-dossier
                    folder_name = relative_path.split('/')[0]
                    folders.add(folder_name)
                else:
                    # C'est un fichier direct
                    items.append({
                        'type': 'file',
                        'name': relative_path,
                        'path': blob.name,
                        'size': blob.size,
                        'last_modified': blob.last_modified,
                        'content_type': blob.content_settings.content_type if blob.content_settings else None
                    })
            
            # Ajouter les dossiers
            for folder in sorted(folders):
                items.append({
                    'type': 'folder',
                    'name': folder,
                    'path': prefix + folder
                })
            
            # Trier : dossiers d'abord, puis fichiers
            items.sort(key=lambda x: (x['type'] != 'folder', x['name']))
            
            return items
            
        except Exception as e:
            logger.error(f"Erreur listing dossier: {e}")
            return []
    
    def download_blob(self, container_name: str, blob_name: str) -> Optional[bytes]:
        """Télécharge un blob et retourne son contenu"""
        if not self.is_connected():
            return None
        
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=container_name,
                blob=blob_name
            )
            
            download_stream = blob_client.download_blob()
            return download_stream.readall()
            
        except ResourceNotFoundError:
            logger.error(f"Blob '{blob_name}' non trouvé dans '{container_name}'")
            return None
        except Exception as e:
            logger.error(f"Erreur téléchargement blob: {e}")
            return None
    
    def upload_blob(self, container_name: str, blob_name: str, data: bytes, 
                   metadata: Optional[Dict[str, str]] = None) -> bool:
        """Upload un blob avec des métadonnées optionnelles"""
        if not self.is_connected():
            return False
        
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=container_name,
                blob=blob_name
            )
            
            blob_client.upload_blob(
                data,
                overwrite=True,
                metadata=metadata
            )
            
            logger.info(f"✅ Blob '{blob_name}' uploadé dans '{container_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Erreur upload blob: {e}")
            return False
    
    def delete_blob(self, container_name: str, blob_name: str) -> bool:
        """Supprime un blob"""
        if not self.is_connected():
            return False
        
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=container_name,
                blob=blob_name
            )
            
            blob_client.delete_blob()
            logger.info(f"✅ Blob '{blob_name}' supprimé de '{container_name}'")
            return True
            
        except ResourceNotFoundError:
            logger.warning(f"Blob '{blob_name}' non trouvé dans '{container_name}'")
            return False
        except Exception as e:
            logger.error(f"Erreur suppression blob: {e}")
            return False
    
    def create_container(self, container_name: str) -> bool:
        """Crée un nouveau container"""
        if not self.is_connected():
            return False
        
        try:
            container_client = self.blob_service_client.create_container(container_name)
            logger.info(f"✅ Container '{container_name}' créé")
            return True
        except Exception as e:
            logger.error(f"Erreur création container: {e}")
            return False
    
    def get_blob_metadata(self, container_name: str, blob_name: str) -> Optional[Dict[str, str]]:
        """Récupère les métadonnées d'un blob"""
        if not self.is_connected():
            return None
        
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=container_name,
                blob=blob_name
            )
            
            properties = blob_client.get_blob_properties()
            return properties.metadata
            
        except Exception as e:
            logger.error(f"Erreur récupération métadonnées: {e}")
            return None