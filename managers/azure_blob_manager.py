# managers/azure_blob_manager.py
"""Gestionnaire Azure Blob Storage avec diagnostics renforcés"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import streamlit as st

logger = logging.getLogger(__name__)

try:
    from azure.core.exceptions import (ClientAuthenticationError,
                                       ResourceNotFoundError)
    from azure.storage.blob import BlobServiceClient, ContainerClient
    AZURE_AVAILABLE = True
    print("[AzureBlobManager] ✅ Azure SDK importé avec succès")
except ImportError as e:
    AZURE_AVAILABLE = False
    print(f"[AzureBlobManager] ❌ Azure SDK non disponible: {e}")

class AzureBlobManager:
    """Gestionnaire pour Azure Blob Storage"""
    
    def __init__(self):
        self.connected = False
        self.blob_service_client = None
        self.connection_error = None
        
        print(f"[AzureBlobManager] Initialisation - AZURE_AVAILABLE: {AZURE_AVAILABLE}")
        
        if not AZURE_AVAILABLE:
            self.connection_error = "SDK Azure non disponible"
            return
        
        # Récupérer la connection string
        connection_string = self._get_connection_string()
        
        if not connection_string:
            self.connection_error = "Connection string non trouvée"
            return
        
        # Valider le format de la connection string
        if not self._validate_connection_string(connection_string):
            self.connection_error = "Format de connection string invalide"
            return
        
        try:
            print("[AzureBlobManager] Création du BlobServiceClient...")
            self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
            
            # Test de connexion
            print("[AzureBlobManager] Test de connexion...")
            self._test_connection()
            
        except ClientAuthenticationError as e:
            self.connection_error = f"Erreur d'authentification: {str(e)}"
            print(f"[AzureBlobManager] ❌ {self.connection_error}")
        except Exception as e:
            self.connection_error = f"Erreur de connexion: {str(e)}"
            print(f"[AzureBlobManager] ❌ {self.connection_error}")
    
    def _get_connection_string(self) -> Optional[str]:
        """Récupère la connection string depuis les variables d'environnement"""
        
        # Méthodes multiples pour récupérer la connection string
        methods = [
            lambda: os.getenv('AZURE_STORAGE_CONNECTION_STRING'),
            lambda: st.secrets.get("AZURE_STORAGE_CONNECTION_STRING") if hasattr(st, 'secrets') else None,
            lambda: os.getenv('azure_storage_connection_string'),
            lambda: os.getenv('AZURE_STORAGE_CONN_STR')
        ]
        
        for i, method in enumerate(methods):
            try:
                conn_str = method()
                if conn_str:
                    print(f"[AzureBlobManager] ✅ Connection string trouvée (méthode {i+1})")
                    print(f"[AzureBlobManager] Connection string: {conn_str[:50]}...")
                    return conn_str
            except Exception as e:
                print(f"[AzureBlobManager] Méthode {i+1} échouée: {e}")
        
        print("[AzureBlobManager] ❌ Aucune connection string trouvée")
        return None
    
    def _validate_connection_string(self, conn_str: str) -> bool:
        """Valide le format de la connection string"""
        required_parts = ['DefaultEndpointsProtocol', 'AccountName', 'AccountKey', 'EndpointSuffix']
        
        for part in required_parts:
            if part not in conn_str:
                print(f"[AzureBlobManager] ❌ Partie manquante dans connection string: {part}")
                return False
        
        print("[AzureBlobManager] ✅ Format de connection string valide")
        return True
    
    def _test_connection(self):
        """Teste la connexion en listant les containers"""
        try:
            containers = list(self.blob_service_client.list_containers())
            self.connected = True
            print(f"[AzureBlobManager] ✅ Connexion réussie! {len(containers)} containers trouvés")
            
            if containers:
                container_names = [c.name for c in containers[:3]]
                print(f"[AzureBlobManager] Premiers containers: {container_names}")
                
        except Exception as e:
            self.connection_error = f"Test de connexion échoué: {str(e)}"
            print(f"[AzureBlobManager] ❌ {self.connection_error}")
            raise
    
    def is_connected(self) -> bool:
        """Vérifie si la connexion est active"""
        return self.connected and self.blob_service_client is not None
    
    def get_connection_error(self) -> Optional[str]:
        """Retourne l'erreur de connexion si applicable"""
        return self.connection_error
    
    def list_containers(self) -> List[str]:
        """Liste tous les containers disponibles"""
        if not self.is_connected():
            print(f"[AzureBlobManager] list_containers: Non connecté - {self.connection_error}")
            return []
        
        try:
            containers = []
            for container in self.blob_service_client.list_containers():
                containers.append(container.name)
            print(f"[AzureBlobManager] list_containers: {len(containers)} containers trouvés")
            return containers
        except Exception as e:
            print(f"[AzureBlobManager] Erreur listing containers: {e}")
            return []
    
    def list_folder_contents(self, container_name: str, folder_path: str = "") -> List[Dict]:
        """Liste le contenu d'un dossier dans un container"""
        if not self.is_connected():
            return []
        
        try:
            container_client = self.blob_service_client.get_container_client(container_name)
            
            prefix = folder_path
            if prefix and not prefix.endswith('/'):
                prefix += '/'
            
            items = []
            folders = set()
            
            for blob in container_client.list_blobs(name_starts_with=prefix):
                relative_path = blob.name[len(prefix):] if prefix else blob.name
                
                if '/' in relative_path:
                    folder_name = relative_path.split('/')[0]
                    folders.add(folder_name)
                else:
                    items.append({
                        'name': relative_path,
                        'path': blob.name,
                        'size': blob.size,
                        'type': 'file',
                        'last_modified': blob.last_modified
                    })
            
            for folder in sorted(folders):
                items.append({
                    'name': folder,
                    'path': prefix + folder,
                    'type': 'folder'
                })
            
            return sorted(items, key=lambda x: (x['type'] == 'file', x['name']))
            
        except Exception as e:
            print(f"[AzureBlobManager] Erreur listing dossier: {e}")
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
            print(f"[AzureBlobManager] Erreur téléchargement blob: {e}")
            return b""