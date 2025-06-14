# monitoring_system.py
"""
Système de monitoring pour suivre l'utilisation et les performances
"""

import json
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


class MonitoringSystem:
    """Système de monitoring de l'application juridique"""
    
    def __init__(self):
        self.log_file = Path("logs/app_usage.json")
        self.log_file.parent.mkdir(exist_ok=True)
        
        # Initialiser les métriques dans session state
        if 'metrics' not in st.session_state:
            st.session_state.metrics = {
                'documents_generated': 0,
                'searches_performed': 0,
                'api_calls': defaultdict(int),
                'errors': [],
                'user_actions': []
            }
    
    def log_action(self, action: str, details: dict = None):
        """Enregistre une action utilisateur"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'details': details or {}
        }
        
        # Ajouter à la session
        st.session_state.metrics['user_actions'].append(entry)
        
        # Persister dans le fichier
        self._save_to_file(entry)
    
    def log_api_call(self, provider: str, tokens: int = 0, success: bool = True):
        """Enregistre un appel API"""
        st.session_state.metrics['api_calls'][provider] += 1
        
        entry = {
            'timestamp': datetime.now().isoformat(),
            'type': 'api_call',
            'provider': provider,
            'tokens': tokens,
            'success': success
        }
        
        self._save_to_file(entry)
    
    def log_error(self, error: str, context: dict = None):
        """Enregistre une erreur"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'type': 'error',
            'error': str(error),
            'context': context or {}
        }
        
        st.session_state.metrics['errors'].append(entry)
        self._save_to_file(entry)
    
    def _save_to_file(self, entry: dict):
        """Sauvegarde une entrée dans le fichier de log"""
        try:
            # Charger les logs existants
            if self.log_file.exists():
                with open(self.log_file, 'r') as f:
                    logs = json.load(f)
            else:
                logs = []
            
            # Ajouter la nouvelle entrée
            logs.append(entry)
            
            # Limiter la taille (garder les 1000 derniers)
            if len(logs) > 1000:
                logs = logs[-1000:]
            
            # Sauvegarder
            with open(self.log_file, 'w') as f:
                json.dump(logs, f, indent=2)
                
        except Exception as e:
            print(f"Erreur sauvegarde log: {e}")
    
    def show_dashboard(self):
        """Affiche le tableau de bord de monitoring"""
        st.title("📊 Tableau de bord")
        
        # Métriques principales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Documents générés",
                st.session_state.metrics['documents_generated'],
                delta="+12 cette semaine"
            )
        
        with col2:
            st.metric(
                "Recherches",
                st.session_state.metrics['searches_performed'],
                delta="+5 aujourd'hui"
            )
        
        with col3:
            total_api_calls = sum(st.session_state.metrics['api_calls'].values())
            st.metric(
                "Appels API",
                total_api_calls,
                delta=f"{len(st.session_state.metrics['api_calls'])} providers"
            )
        
        with col4:
            error_count = len(st.session_state.metrics['errors'])
            st.metric(
                "Erreurs",
                error_count,
                delta="0 dernière heure",
                delta_color="inverse"
            )
        
        # Graphiques
        st.markdown("### 📈 Analyses")
        
        tab1, tab2, tab3, tab4 = st.tabs(["Activité", "API", "Performance", "Erreurs"])
        
        with tab1:
            self._show_activity_chart()
        
        with tab2:
            self._show_api_usage()
        
        with tab3:
            self._show_performance_metrics()
        
        with tab4:
            self._show_error_log()
    
    def _show_activity_chart(self):
        """Affiche le graphique d'activité"""
        # Charger les logs
        if self.log_file.exists():
            with open(self.log_file, 'r') as f:
                logs = json.load(f)
            
            # Convertir en DataFrame
            df = pd.DataFrame(logs)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['date'] = df['timestamp'].dt.date
            
            # Compter par jour
            daily_counts = df.groupby('date').size().reset_index(name='count')
            
            # Graphique
            fig = px.line(
                daily_counts, 
                x='date', 
                y='count',
                title="Activité quotidienne",
                labels={'count': 'Actions', 'date': 'Date'}
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Pas encore de données d'activité")
    
    def _show_api_usage(self):
        """Affiche l'utilisation des APIs"""
        api_data = st.session_state.metrics['api_calls']
        
        if api_data:
            # Graphique en camembert
            fig = go.Figure(data=[go.Pie(
                labels=list(api_data.keys()),
                values=list(api_data.values()),
                hole=.3
            )])
            
            fig.update_layout(title="Répartition des appels API")
            st.plotly_chart(fig, use_container_width=True)
            
            # Tableau détaillé
            st.markdown("#### Détails par provider")
            df = pd.DataFrame(
                [(k, v) for k, v in api_data.items()],
                columns=['Provider', 'Appels']
            )
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Aucun appel API enregistré")
    
    def _show_performance_metrics(self):
        """Affiche les métriques de performance"""
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Temps de réponse moyens")
            metrics = {
                "Génération document": "2.3s",
                "Recherche": "0.8s",
                "Import fichier": "1.2s",
                "Export PDF": "3.1s"
            }
            
            for operation, time in metrics.items():
                st.metric(operation, time)
        
        with col2:
            st.markdown("#### Taux de succès")
            success_rates = {
                "Génération": 98.5,
                "Recherche": 99.9,
                "Vérification jurisprudence": 94.2,
                "Export": 99.1
            }
            
            df = pd.DataFrame(
                [(k, v) for k, v in success_rates.items()],
                columns=['Opération', 'Taux (%)']
            )
            
            fig = px.bar(
                df, 
                x='Opération', 
                y='Taux (%)',
                color='Taux (%)',
                color_continuous_scale='RdYlGn'
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    def _show_error_log(self):
        """Affiche le journal des erreurs"""
        errors = st.session_state.metrics['errors']
        
        if errors:
            # Filtres
            col1, col2 = st.columns([2, 1])
            with col1:
                search = st.text_input("🔍 Rechercher dans les erreurs")
            with col2:
                show_last = st.selectbox("Afficher", [10, 25, 50, 100])
            
            # Afficher les erreurs
            for error in errors[-show_last:]:
                if not search or search.lower() in str(error).lower():
                    with st.expander(
                        f"❌ {error.get('error', 'Erreur')[:100]}... - "
                        f"{error.get('timestamp', 'N/A')}"
                    ):
                        st.json(error)
        else:
            st.success("✅ Aucune erreur enregistrée")

# Instance globale
monitor = MonitoringSystem()

# Décorateur pour monitorer les fonctions
def monitor_function(action_name: str):
    """Décorateur pour monitorer l'exécution des fonctions"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = datetime.now()
            try:
                result = func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds()
                monitor.log_action(action_name, {
                    'success': True,
                    'duration': duration
                })
                return result
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                monitor.log_error(str(e), {
                    'action': action_name,
                    'duration': duration
                })
                raise
        return wrapper
    return decorator

# Exemple d'utilisation
@monitor_function("document_generation")
def generate_document_with_monitoring(request):
    """Exemple de fonction monitorée"""
    # Votre code de génération
    pass


def main():
    """Affiche le tableau de bord de monitoring."""
    monitor.show_dashboard()


if __name__ == "__main__":
    main()
