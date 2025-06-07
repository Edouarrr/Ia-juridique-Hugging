# managers/azure_blob_manager.py
"""Gestionnaire Azure Blob Storage"""

import os
import streamlit as st
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

try:
    from azure.storage.blob import BlobServiceClient, ContainerClient
    from azure.core.exceptions import ResourceNotFoundError
    AZURE_AVAILABLE = True
    print("[AzureBlobManager] Azure SDK importé avec succès")
except ImportError as e:
    AZURE_AVAILABLE = False
    print(f"[AzureBlobManager] Azure SDK non disponible: {e}")

class AzureBlobManager:
    """Gestionnaire pour Azure Blob Storage"""
    
    def __init__(self):
        self.connected = False
        self.blob_service_client = None
        
        print(f"[AzureBlobManager] Initialisation - AZURE_AVAILABLE: {AZURE_AVAILABLE}")
        
        if not AZURE_AVAILABLE:
            print("[AzureBlobManager] SDK Azure non disponible, arrêt de l'initialisation")
            return
        
        # Essayer plusieurs méthodes pour obtenir la connection string
        connection_string = None
        
        # Méthode 1: Variable d'environnement standard
        connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        if connection_string:
            print("[AzureBlobManager] Connection string trouvée via os.getenv")
        
        # Méthode 2: st.secrets (pour Hugging Face Spaces)
        if not connection_string:
            try:
                connection_string = st.secrets.get("AZURE_STORAGE_CONNECTION_STRING")
                if connection_string:
                    print("[AzureBlobManager] Connection string trouvée via st.secrets")
            except Exception as e:
                print(f"[AzureBlobManager] st.secrets non disponible: {e}")
        
        # Méthode 3: Vérifier les secrets avec différentes clés possibles
        if not connection_string:
            possible_keys = [
                'azure_storage_connection_string',
                'AZURE_STORAGE_CONNECTION_STRING',
                'AzureStorageConnectionString',
                'azure_storage'
            ]
            for key in possible_keys:
                try:
                    connection_string = os.getenv(key) or st.secrets.get(key)
                    if connection_string:
                        print(f"[AzureBlobManager] Connection string trouvée avec la clé: {key}")
                        break
                except:
                    pass
        
        if not connection_string:
            print("[AzureBlobManager] Aucune connection string trouvée")
            print("[AzureBlobManager] Variables d'environnement disponibles:", list(os.environ.keys())[:10])
            return
        
        # Vérifier le format de la connection string
        print(f"[AzureBlobManager] Connection string commence par: {connection_string[:50]}...")
        
        try:
            # Créer le client
            self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
            print("[AzureBlobManager] BlobServiceClient créé")
            
            # Tester la connexion en listant les containers
            containers = []
            try:
                for container in self.blob_service_client.list_containers():
                    containers.append(container.name)
                    if len(containers) >= 5:  # Limiter pour le test
                        break
                
                self.connected = True
                print(f"[AzureBlobManager] ✅ Connexion réussie! {len(containers)} containers trouvés")
                if containers:
                    print(f"[AzureBlobManager] Premiers containers: {containers}")
                    
            except Exception as e:
                print(f"[AzureBlobManager] ❌ Erreur lors du test de connexion: {type(e).__name__}: {str(e)}")
                self.connected = False
                
        except Exception as e:
            print(f"[AzureBlobManager] ❌ Erreur création BlobServiceClient: {type(e).__name__}: {str(e)}")
            self.connected = False
    
    def is_connected(self) -> bool:
        """Vérifie si la connexion est active"""
        return self.connected and self.blob_service_client is not None
    
    def list_containers(self) -> List[str]:
        """Liste tous les containers disponibles"""
        if not self.is_connected():
            print("[AzureBlobManager] list_containers: Non connecté")
            return []
        
        try:
            containers = []
            for container in self.blob_service_client.list_containers():
                containers.append(container.name)
            print(f"[AzureBlobManager] list_containers: {len(containers)} containers trouvés")
            return containers
        except Exception as e:
            print(f"[AzureBlobManager] Erreur listing containers: {type(e).__name__}: {str(e)}")
            return []
    
    def list_folder_contents(self, container_name: str, folder_path: str = "") -> List[Dict]:
        """Liste le contenu d'un dossier dans un container"""
        if not self.is_connected():
            return []
        
        try:
            container_client = self.blob_service_client.get_container_client(container_name)
            
            # Normaliser le chemin
            prefix = folder_path
            if prefix and not prefix.endswith('/'):
                prefix += '/'
            
            items = []
            folders = set()
            
            # Lister les blobs
            for blob in container_client.list_blobs(name_starts_with=prefix):
                # Obtenir le chemin relatif
                relative_path = blob.name[len(prefix):] if prefix else blob.name
                
                # Vérifier si c'est un dossier
                if '/' in relative_path:
                    folder_name = relative_path.split('/')[0]
                    folders.add(folder_name)
                else:
                    # C'est un fichier
                    items.append({
                        'name': relative_path,
                        'path': blob.name,
                        'size': blob.size,
                        'type': 'file',
                        'last_modified': blob.last_modified
                    })
            
            # Ajouter les dossiers
            for folder in sorted(folders):
                items.append({
                    'name': folder,
                    'path': prefix + folder,
                    'type': 'folder'
                })
            
            return sorted(items, key=lambda x: (x['type'] == 'file', x['name']))
            
        except Exception as e:
            logger.error(f"Erreur listing dossier: {e}")
            return []
    
    def download_blob(self, container_name: str, blob_path: str) -> bytes:
        """Télécharge un blob et retourne son contenu"""
        if not self.is_connected():
            return b""
        
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=container_name,
                blob=blob_path
            )
            
            return blob_client.download_blob().readall()
            
        except Exception as e:
            logger.error(f"Erreur téléchargement blob: {e}")
            return b""
    
    def upload_blob(self, container_name: str, blob_path: str, data: bytes) -> bool:
        """Upload des données vers un blob"""
        if not self.is_connected():
            return False
        
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=container_name,
                blob=blob_path
            )
            
            blob_client.upload_blob(data, overwrite=True)
            return True
            
        except Exception as e:
            logger.error(f"Erreur upload blob: {e}")
            return False
    
    def search_blobs(self, container_name: str, search_term: str, max_results: int = 50) -> List[Dict]:
        """Recherche des blobs par nom"""
        if not self.is_connected():
            return []
        
        try:
            container_client = self.blob_service_client.get_container_client(container_name)
            results = []
            
            for blob in container_client.list_blobs():
                if search_term.lower() in blob.name.lower():
                    results.append({
                        'name': blob.name,
                        'size': blob.size,
                        'last_modified': blob.last_modified,
                        'container': container_name
                    })
                    
                    if len(results) >= max_results:
                        break
            
            return results
            
        except Exception as e:
            logger.error(f"Erreur recherche blobs: {e}")
            return []