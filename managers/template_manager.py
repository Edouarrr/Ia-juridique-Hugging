# managers/template_manager.py
"""Gestionnaire des templates de documents juridiques"""

import streamlit as st
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import json
import uuid

from modules.dataclasses import (
    DocumentTemplate, 
    TemplateDocument,
    TypeDocument,
    StyleRedaction
)
from config.app_config import DOCUMENT_TEMPLATES, LEGAL_PHRASES

class TemplateManager:
    """Gestionnaire centralisé des templates de documents"""
    
    def __init__(self):
        # Templates par défaut depuis la config
        self.default_templates = DOCUMENT_TEMPLATES
        self.legal_phrases = LEGAL_PHRASES
        
        # Initialiser le session state
        if 'custom_templates' not in st.session_state:
            st.session_state.custom_templates = {}
        
        if 'template_history' not in st.session_state:
            st.session_state.template_history = []
    
    def get_template(self, document_type: str) -> Dict[str, Any]:
        """Récupère un template par type de document"""
        # Chercher d'abord dans les templates personnalisés
        if document_type in st.session_state.custom_templates:
            return st.session_state.custom_templates[document_type]
        
        # Sinon utiliser le template par défaut
        return self.default_templates.get(document_type, self._get_generic_template())
    
    def _get_generic_template(self) -> Dict[str, Any]:
        """Template générique si aucun n'est défini"""
        return {
            "structure": [
                "INTRODUCTION",
                "DÉVELOPPEMENT",
                "CONCLUSION"
            ],
            "required_sections": ["INTRODUCTION", "CONCLUSION"]
        }
    
    def list_available_templates(self) -> List[str]:
        """Liste tous les templates disponibles"""
        default_types = list(self.default_templates.keys())
        custom_types = list(st.session_state.custom_templates.keys())
        return list(set(default_types + custom_types))
    
    def create_custom_template(self, name: str, template_data: Dict[str, Any]) -> bool:
        """Crée un nouveau template personnalisé"""
        try:
            template_id = f"custom_{name}_{uuid.uuid4().hex[:8]}"
            
            template = DocumentTemplate(
                id=template_id,
                name=name,
                type_document=template_data.get('type_document', 'autre'),
                structure=template_data.get('structure', []),
                required_sections=template_data.get('required_sections', []),
                variables=template_data.get('variables', {}),
                style_defaut=template_data.get('style_defaut', StyleRedaction.PROFESSIONNEL),
                metadata={
                    'created_at': datetime.now().isoformat(),
                    'created_by': 'user',
                    'custom': True
                }
            )
            
            st.session_state.custom_templates[name] = {
                "structure": template.structure,
                "required_sections": template.required_sections,
                "variables": template.variables,
                "metadata": template.metadata
            }
            
            # Ajouter à l'historique
            st.session_state.template_history.append({
                'action': 'create',
                'template_name': name,
                'timestamp': datetime.now(),
                'data': template_data
            })
            
            return True
            
        except Exception as e:
            st.error(f"Erreur lors de la création du template : {e}")
            return False
    
    def update_template(self, name: str, updates: Dict[str, Any]) -> bool:
        """Met à jour un template existant"""
        if name not in st.session_state.custom_templates:
            st.error(f"Template '{name}' non trouvé")
            return False
        
        try:
            template = st.session_state.custom_templates[name]
            template.update(updates)
            template['metadata']['updated_at'] = datetime.now().isoformat()
            
            # Ajouter à l'historique
            st.session_state.template_history.append({
                'action': 'update',
                'template_name': name,
                'timestamp': datetime.now(),
                'updates': updates
            })
            
            return True
            
        except Exception as e:
            st.error(f"Erreur lors de la mise à jour : {e}")
            return False
    
    def delete_template(self, name: str) -> bool:
        """Supprime un template personnalisé"""
        if name not in st.session_state.custom_templates:
            return False
        
        del st.session_state.custom_templates[name]
        
        # Ajouter à l'historique
        st.session_state.template_history.append({
            'action': 'delete',
            'template_name': name,
            'timestamp': datetime.now()
        })
        
        return True
    
    def get_template_variables(self, document_type: str) -> Dict[str, str]:
        """Récupère les variables disponibles pour un type de document"""
        template = self.get_template(document_type)
        
        # Variables par défaut
        default_vars = {
            'date': datetime.now().strftime('%d/%m/%Y'),
            'tribunal': '[TRIBUNAL]',
            'numero_rg': '[N° RG]',
            'demandeur': '[DEMANDEUR]',
            'defendeur': '[DÉFENDEUR]',
            'avocat': '[AVOCAT]'
        }
        
        # Ajouter les variables spécifiques du template
        if 'variables' in template:
            default_vars.update(template['variables'])
        
        return default_vars
    
    def apply_template(self, document_type: str, content_data: Dict[str, Any]) -> str:
        """Applique un template pour générer le contenu structuré"""
        template = self.get_template(document_type)
        structure = template.get('structure', [])
        
        # Construire le document section par section
        document_parts = []
        
        for section in structure:
            if section in content_data:
                document_parts.append(f"\n{section}\n")
                document_parts.append("=" * len(section))
                document_parts.append(f"\n{content_data[section]}\n")
        
        return "\n".join(document_parts)
    
    def get_legal_phrases(self, category: str, document_type: Optional[str] = None) -> List[str]:
        """Récupère les phrases juridiques types"""
        if document_type and category in self.legal_phrases:
            if document_type in self.legal_phrases[category]:
                return self.legal_phrases[category][document_type]
        
        # Retourner toutes les phrases de la catégorie si pas de type spécifique
        if category in self.legal_phrases:
            if isinstance(self.legal_phrases[category], dict):
                all_phrases = []
                for phrases in self.legal_phrases[category].values():
                    all_phrases.extend(phrases)
                return all_phrases
            else:
                return self.legal_phrases[category]
        
        return []
    
    def export_templates(self) -> Dict[str, Any]:
        """Exporte tous les templates personnalisés"""
        return {
            'custom_templates': st.session_state.custom_templates,
            'export_date': datetime.now().isoformat(),
            'template_count': len(st.session_state.custom_templates)
        }
    
    def import_templates(self, import_data: Dict[str, Any]) -> bool:
        """Importe des templates depuis un export"""
        try:
            if 'custom_templates' in import_data:
                for name, template in import_data['custom_templates'].items():
                    # Éviter d'écraser les templates existants
                    if name not in st.session_state.custom_templates:
                        st.session_state.custom_templates[name] = template
                    else:
                        # Renommer si conflit
                        new_name = f"{name}_imported_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                        st.session_state.custom_templates[new_name] = template
                
                return True
                
        except Exception as e:
            st.error(f"Erreur lors de l'import : {e}")
            return False
    
    def get_template_preview(self, document_type: str) -> str:
        """Génère un aperçu du template"""
        template = self.get_template(document_type)
        structure = template.get('structure', [])
        
        preview_lines = [f"Template : {document_type.upper()}", "=" * 40, ""]
        preview_lines.append("Structure :")
        
        for i, section in enumerate(structure, 1):
            required = " (obligatoire)" if section in template.get('required_sections', []) else ""
            preview_lines.append(f"{i}. {section}{required}")
        
        return "\n".join(preview_lines)