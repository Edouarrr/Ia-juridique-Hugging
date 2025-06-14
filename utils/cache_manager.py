# utils/cache_manager.py
"""
Système de cache pour optimiser les performances du module juridique
"""

import hashlib
import json
import os
import pickle
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Union

import streamlit as st

# Configuration du cache
CACHE_DIR = "cache_juridique"
CACHE_DURATION = {
    'acte_genere': timedelta(hours=24),        # Actes générés : 24h
    'analyse_requete': timedelta(hours=1),      # Analyses : 1h
    'enrichissement': timedelta(days=7),        # Infos sociétés : 7 jours
    'jurisprudence': timedelta(days=30),        # Jurisprudences : 30 jours
    'template': timedelta(days=90),             # Templates : 90 jours
    'document': timedelta(days=7),              # Documents : 7 jours
    'search': timedelta(hours=2),               # Recherches : 2 heures
    'general': timedelta(hours=6)               # Général : 6 heures
}


class CacheJuridique:
    """Gestionnaire de cache pour les opérations juridiques"""
    
    def __init__(self, cache_dir: str = CACHE_DIR):
        self.cache_dir = cache_dir
        self._ensure_cache_dir()
        self.memory_cache = {}  # Cache en mémoire pour la session
        self.stats = {
            'hits': 0,
            'misses': 0,
            'writes': 0,
            'errors': 0
        }
    
    def _ensure_cache_dir(self):
        """Crée le répertoire de cache s'il n'existe pas"""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def _get_cache_key(self, key: str, cache_type: str) -> str:
        """Génère une clé de cache unique"""
        # Hasher la clé pour éviter les problèmes de noms de fichiers
        key_data = f"{cache_type}:{key}"
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        return f"{cache_type}_{key_hash}"
    
    def _get_cache_path(self, cache_key: str) -> str:
        """Retourne le chemin complet du fichier de cache"""
        return os.path.join(self.cache_dir, f"{cache_key}.cache")
    
    def get(self, key: str, cache_type: str = 'general') -> Optional[Any]:
        """Récupère une valeur du cache"""
        try:
            # Vérifier d'abord le cache mémoire
            memory_key = f"{cache_type}:{key}"
            if memory_key in self.memory_cache:
                entry = self.memory_cache[memory_key]
                if self._is_valid_entry(entry, cache_type):
                    self.stats['hits'] += 1
                    return entry['data']
            
            # Sinon, vérifier le cache disque
            cache_key = self._get_cache_key(key, cache_type)
            cache_path = self._get_cache_path(cache_key)
            
            if os.path.exists(cache_path):
                try:
                    with open(cache_path, 'rb') as f:
                        entry = pickle.load(f)
                    
                    if self._is_valid_entry(entry, cache_type):
                        # Mettre aussi en cache mémoire
                        self.memory_cache[memory_key] = entry
                        self.stats['hits'] += 1
                        return entry['data']
                    else:
                        # Supprimer l'entrée expirée
                        os.remove(cache_path)
                        
                except Exception as e:
                    self.stats['errors'] += 1
                    print(f"Erreur lecture cache: {e}")
            
            self.stats['misses'] += 1
            return None
            
        except Exception as e:
            self.stats['errors'] += 1
            print(f"Erreur dans get: {e}")
            return None
    
    def set(self, key: str, data: Any, cache_type: str = 'general', metadata: Dict = None):
        """Stocke une valeur dans le cache"""
        try:
            entry = {
                'data': data,
                'timestamp': datetime.now().isoformat(),
                'type': cache_type,
                'metadata': metadata or {}
            }
            
            # Stocker en cache mémoire
            memory_key = f"{cache_type}:{key}"
            self.memory_cache[memory_key] = entry
            
            # Stocker sur disque
            cache_key = self._get_cache_key(key, cache_type)
            cache_path = self._get_cache_path(cache_key)
            
            try:
                with open(cache_path, 'wb') as f:
                    pickle.dump(entry, f)
                self.stats['writes'] += 1
            except Exception as e:
                self.stats['errors'] += 1
                print(f"Erreur écriture cache: {e}")
                
        except Exception as e:
            self.stats['errors'] += 1
            print(f"Erreur dans set: {e}")
    
    def _is_valid_entry(self, entry: Dict, cache_type: str) -> bool:
        """Vérifie si une entrée de cache est encore valide"""
        if 'timestamp' not in entry:
            return False
        
        try:
            timestamp = datetime.fromisoformat(entry['timestamp'])
            duration = CACHE_DURATION.get(cache_type, timedelta(hours=1))
            return datetime.now() - timestamp < duration
        except:
            return False
    
    def clear(self, cache_type: Optional[str] = None):
        """Efface le cache (tout ou un type spécifique)"""
        try:
            # Effacer le cache mémoire
            if cache_type:
                keys_to_remove = [k for k in self.memory_cache.keys() 
                                if k.startswith(f"{cache_type}:")]
                for k in keys_to_remove:
                    del self.memory_cache[k]
            else:
                self.memory_cache.clear()
            
            # Effacer le cache disque
            if os.path.exists(self.cache_dir):
                for filename in os.listdir(self.cache_dir):
                    if cache_type and not filename.startswith(f"{cache_type}_"):
                        continue
                    
                    file_path = os.path.join(self.cache_dir, filename)
                    try:
                        os.remove(file_path)
                    except:
                        pass
                        
        except Exception as e:
            print(f"Erreur dans clear: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne des statistiques sur le cache"""
        stats = {
            'memory_entries': len(self.memory_cache),
            'disk_entries': 0,
            'total_size': 0,
            'by_type': {},
            'performance': self.stats.copy()
        }
        
        if os.path.exists(self.cache_dir):
            for filename in os.listdir(self.cache_dir):
                file_path = os.path.join(self.cache_dir, filename)
                try:
                    stats['disk_entries'] += 1
                    stats['total_size'] += os.path.getsize(file_path)
                    
                    # Compter par type
                    cache_type = filename.split('_')[0]
                    if cache_type not in stats['by_type']:
                        stats['by_type'][cache_type] = 0
                    stats['by_type'][cache_type] += 1
                except:
                    pass
        
        # Calculer le taux de réussite
        total_requests = stats['performance']['hits'] + stats['performance']['misses']
        if total_requests > 0:
            stats['performance']['hit_rate'] = stats['performance']['hits'] / total_requests
        else:
            stats['performance']['hit_rate'] = 0
        
        # Formater la taille
        stats['total_size_readable'] = self._format_size(stats['total_size'])
        
        return stats
    
    def _format_size(self, size_bytes: int) -> str:
        """Formate une taille en bytes en format lisible"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"
    
    def cleanup_expired(self):
        """Nettoie les entrées expirées du cache"""
        if not os.path.exists(self.cache_dir):
            return
        
        cleaned = 0
        for filename in os.listdir(self.cache_dir):
            file_path = os.path.join(self.cache_dir, filename)
            
            try:
                with open(file_path, 'rb') as f:
                    entry = pickle.load(f)
                
                # Déterminer le type de cache
                cache_type = filename.split('_')[0]
                
                if not self._is_valid_entry(entry, cache_type):
                    os.remove(file_path)
                    cleaned += 1
                    
            except:
                # Supprimer les fichiers corrompus
                try:
                    os.remove(file_path)
                    cleaned += 1
                except:
                    pass
        
        return cleaned


# Instance globale du cache
_cache_instance = None

def get_cache() -> CacheJuridique:
    """Retourne l'instance globale du cache"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = CacheJuridique()
    return _cache_instance


# ========================= DÉCORATEURS DE CACHE =========================

def cache_result(cache_type: str = 'general', key_generator: Callable = None):
    """
    Décorateur pour mettre en cache le résultat d'une fonction
    
    Args:
        cache_type: Type de cache à utiliser
        key_generator: Fonction pour générer la clé de cache
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Générer la clé de cache
            if key_generator:
                cache_key = key_generator(*args, **kwargs)
            else:
                # Clé par défaut basée sur les arguments
                key_parts = [func.__name__]
                key_parts.extend(str(arg) for arg in args if not callable(arg))
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = "|".join(key_parts)
            
            # Vérifier le cache
            cache = get_cache()
            cached_result = cache.get(cache_key, cache_type)
            
            if cached_result is not None:
                return cached_result
            
            # Sinon, exécuter la fonction
            result = func(*args, **kwargs)
            
            # Mettre en cache le résultat
            cache.set(cache_key, result, cache_type)
            
            return result
        
        return wrapper
    return decorator


def cache_streamlit(cache_type: str = 'general', show_spinner: bool = True):
    """Décorateur spécifique pour Streamlit avec gestion du spinner"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Générer la clé
            key_parts = [func.__name__]
            key_parts.extend(str(arg) for arg in args if not callable(arg))
            cache_key = "|".join(key_parts)
            
            # Vérifier le cache
            cache = get_cache()
            cached_result = cache.get(cache_key, cache_type)
            
            if cached_result is not None:
                st.info("📦 Résultat chargé depuis le cache")
                return cached_result
            
            # Exécuter avec spinner si demandé
            if show_spinner:
                with st.spinner(f"⏳ Génération en cours..."):
                    result = func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # Mettre en cache
            cache.set(cache_key, result, cache_type)
            
            return result
        
        return wrapper
    return decorator


# ========================= CACHE SPÉCIALISÉ =========================

class CacheActesJuridiques:
    """Cache spécialisé pour les actes juridiques générés"""
    
    def __init__(self):
        self.cache = get_cache()
    
    def get_acte(self, type_acte: str, parties: Dict, infractions: List[str]) -> Optional[Any]:
        """Récupère un acte en cache"""
        key_data = {
            'type': type_acte,
            'demandeurs': sorted(parties.get('demandeurs', [])),
            'defendeurs': sorted(parties.get('defendeurs', [])),
            'infractions': sorted(infractions)
        }
        
        key = json.dumps(key_data, sort_keys=True)
        return self.cache.get(key, 'acte_genere')
    
    def save_acte(self, acte: Any, type_acte: str, parties: Dict, infractions: List[str]):
        """Sauvegarde un acte en cache"""
        key_data = {
            'type': type_acte,
            'demandeurs': sorted(parties.get('demandeurs', [])),
            'defendeurs': sorted(parties.get('defendeurs', [])),
            'infractions': sorted(infractions)
        }
        
        key = json.dumps(key_data, sort_keys=True)
        metadata = {
            'type_acte': type_acte,
            'nb_parties': len(parties.get('demandeurs', [])) + len(parties.get('defendeurs', [])),
            'nb_infractions': len(infractions)
        }
        self.cache.set(key, acte, 'acte_genere', metadata)
    
    def get_recent_actes(self, limit: int = 10) -> List[Dict]:
        """Récupère les actes récents depuis le cache"""
        recent = []
        
        if os.path.exists(self.cache.cache_dir):
            files = []
            
            # Lister tous les fichiers d'actes
            for filename in os.listdir(self.cache.cache_dir):
                if filename.startswith('acte_genere_'):
                    file_path = os.path.join(self.cache.cache_dir, filename)
                    files.append((file_path, os.path.getmtime(file_path)))
            
            # Trier par date de modification
            files.sort(key=lambda x: x[1], reverse=True)
            
            # Charger les plus récents
            for file_path, mtime in files[:limit]:
                try:
                    with open(file_path, 'rb') as f:
                        entry = pickle.load(f)
                    
                    if self.cache._is_valid_entry(entry, 'acte_genere'):
                        recent.append({
                            'acte': entry['data'],
                            'date': datetime.fromtimestamp(mtime),
                            'metadata': entry.get('metadata', {})
                        })
                except:
                    pass
        
        return recent


# ========================= INTERFACE STREAMLIT =========================

def show_cache_management():
    """Interface de gestion du cache dans Streamlit"""
    st.header("🗄️ Gestion du cache")
    
    cache = get_cache()
    stats = cache.get_stats()
    
    # Afficher les statistiques
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Entrées mémoire", stats['memory_entries'])
    
    with col2:
        st.metric("Entrées disque", stats['disk_entries'])
    
    with col3:
        st.metric("Taille totale", stats['total_size_readable'])
    
    with col4:
        hit_rate = stats['performance']['hit_rate']
        st.metric("Taux de réussite", f"{hit_rate:.1%}")
    
    # Détails par type
    if stats['by_type']:
        st.subheader("📊 Répartition par type")
        
        for cache_type, count in stats['by_type'].items():
            duration = CACHE_DURATION.get(cache_type, timedelta(hours=1))
            duration_str = f"{duration.days}j" if duration.days > 0 else f"{duration.seconds//3600}h"
            st.write(f"• **{cache_type}:** {count} entrées (durée: {duration_str})")
    
    # Actions
    st.subheader("🎯 Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🧹 Nettoyer expiré", key="cleanup_cache"):
            with st.spinner("Nettoyage..."):
                cleaned = cache.cleanup_expired()
            st.success(f"✅ {cleaned} entrées expirées supprimées")
    
    with col2:
        cache_type_to_clear = st.selectbox(
            "Type à effacer",
            ["Tout"] + list(CACHE_DURATION.keys()),
            key="cache_type_clear"
        )
    
    with col3:
        if st.button("🗑️ Effacer le cache", key="clear_cache"):
            if cache_type_to_clear == "Tout":
                cache.clear()
            else:
                cache.clear(cache_type_to_clear)
            st.success("✅ Cache effacé")
            st.rerun()
    
    # Performance
    st.subheader("📈 Performance")
    
    perf = stats['performance']
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Hits", perf['hits'])
    
    with col2:
        st.metric("Misses", perf['misses'])
    
    with col3:
        st.metric("Écritures", perf['writes'])
    
    with col4:
        st.metric("Erreurs", perf['errors'])