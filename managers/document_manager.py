# managers/document_manager.py (fonction display_import_interface)
"""Gestionnaire de documents - Import, export et traitement"""

import streamlit as st
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import json
from datetime import datetime
import io
import base64
from pathlib import Path
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def display_import_interface():
    """Affiche l'interface d'import de documents"""
    st.markdown("### 📤 Import de documents")
    
    # Zone de drag & drop
    uploaded_files = st.file_uploader(
        "Glissez vos fichiers ici ou cliquez pour parcourir",
        type=['pdf', 'docx', 'txt', 'xlsx', 'xls', 'json', 'csv'],
        accept_multiple_files=True,
        help="Formats supportés : PDF, Word, Excel, TXT, JSON, CSV"
    )
    
    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} fichier(s) sélectionné(s)")
        
        # Prévisualisation et options
        for file in uploaded_files:
            with st.expander(f"📄 {file.name} ({file.size / 1024:.2f} KB)"):
                file_type = file.type
                
                # Aperçu selon le type
                if file_type == "text/plain":
                    content = file.read().decode('utf-8')
                    st.text_area("Aperçu", content[:1000], height=200)
                    
                elif file_type == "application/json":
                    content = json.load(file)
                    st.json(content)
                    
                elif file_type in ["application/vnd.ms-excel", 
                                  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]:
                    df = pd.read_excel(file)
                    st.dataframe(df.head(10))
                    st.caption(f"Dimensions : {df.shape[0]} lignes × {df.shape[1]} colonnes")
                    
                elif file_type == "text/csv":
                    df = pd.read_csv(file)
                    st.dataframe(df.head(10))
                    
                else:
                    st.info(f"Type : {file_type}")
                    st.info("Prévisualisation non disponible pour ce type de fichier")
                
                # Options d'import
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"Importer", key=f"import_{file.name}"):
                        # Ici on pourrait traiter le fichier
                        st.session_state.imported_content = file.read()
                        st.success(f"✅ {file.name} importé")
                
                with col2:
                    if st.button(f"Ignorer", key=f"ignore_{file.name}"):
                        st.info(f"❌ {file.name} ignoré")

# Import des bibliothèques de traitement de documents
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
import PyPDF2
from PIL import Image
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment

from models.dataclasses import AnalyseJuridique, CasJuridique, DocumentJuridique

logger = logging.getLogger(__name__)

class DocumentManager:
    """Gestionnaire centralisé pour tous les documents"""
    
    SUPPORTED_FORMATS = {
        'import': ['.pdf', '.docx', '.txt', '.json', '.xlsx', '.csv'],
        'export': ['pdf', 'docx', 'xlsx', 'json', 'txt']
    }
    
    def __init__(self):
        self.imported_documents = []
        self.processed_texts = []
        
    def import_document(self, file) -> Tuple[bool, str, str]:
        """
        Importe un document et extrait son contenu
        Retourne: (succès, contenu, message)
        """
        try:
            file_extension = Path(file.name).suffix.lower()
            
            if file_extension not in self.SUPPORTED_FORMATS['import']:
                return False, "", f"Format non supporté: {file_extension}"
            
            # Traitement selon le type
            if file_extension == '.pdf':
                content = self._extract_pdf_content(file)
            elif file_extension == '.docx':
                content = self._extract_docx_content(file)
            elif file_extension == '.txt':
                content = str(file.read(), 'utf-8')
            elif file_extension == '.json':
                content = self._extract_json_content(file)
            elif file_extension in ['.xlsx', '.csv']:
                content = self._extract_table_content(file, file_extension)
            else:
                return False, "", "Format non reconnu"
            
            # Stocker le document importé
            self.imported_documents.append({
                'filename': file.name,
                'content': content,
                'import_date': datetime.now(),
                'size': file.size
            })
            
            return True, content, f"Document '{file.name}' importé avec succès"
            
        except Exception as e:
            logger.error(f"Erreur import document: {e}")
            return False, "", f"Erreur lors de l'import: {str(e)}"
    
    def _extract_pdf_content(self, file) -> str:
        """Extrait le texte d'un PDF"""
        try:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            
            for page_num, page in enumerate(pdf_reader.pages):
                text += f"\n--- Page {page_num + 1} ---\n"
                text += page.extract_text()
                
            return text.strip()
        except Exception as e:
            logger.error(f"Erreur extraction PDF: {e}")
            raise
    
    def _extract_docx_content(self, file) -> str:
        """Extrait le texte d'un DOCX"""
        try:
            doc = Document(file)
            text = ""
            
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
                
            # Extraire aussi les tableaux
            for table in doc.tables:
                for row in table.rows:
                    row_text = "\t".join(cell.text for cell in row.cells)
                    text += row_text + "\n"
                    
            return text.strip()
        except Exception as e:
            logger.error(f"Erreur extraction DOCX: {e}")
            raise
    
    def _extract_json_content(self, file) -> str:
        """Extrait et formate le contenu JSON"""
        try:
            data = json.load(file)
            return json.dumps(data, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erreur extraction JSON: {e}")
            raise
    
    def _extract_table_content(self, file, extension: str) -> str:
        """Extrait le contenu d'un fichier tabulaire"""
        try:
            if extension == '.csv':
                df = pd.read_csv(file)
            else:  # xlsx
                df = pd.read_excel(file)
                
            # Convertir en texte structuré
            text = f"Tableau avec {len(df)} lignes et {len(df.columns)} colonnes\n\n"
            text += "Colonnes: " + ", ".join(df.columns) + "\n\n"
            
            # Résumé des données
            text += "Aperçu des données:\n"
            text += df.head(10).to_string()
            
            return text
        except Exception as e:
            logger.error(f"Erreur extraction tableau: {e}")
            raise
    
    def export_analysis(
        self,
        analysis: AnalyseJuridique,
        format: str,
        include_metadata: bool = True
    ) -> Tuple[bytes, str]:
        """
        Exporte une analyse dans le format demandé
        Retourne: (contenu_bytes, nom_fichier)
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"analyse_juridique_{timestamp}"
        
        if format == 'pdf':
            # Note: Pour un vrai PDF, utiliser reportlab ou weasyprint
            # Ici on fait une version simplifiée
            content = self._create_pdf_content(analysis, include_metadata)
            filename = f"{base_filename}.pdf"
        elif format == 'docx':
            content = self._create_docx_content(analysis, include_metadata)
            filename = f"{base_filename}.docx"
        elif format == 'xlsx':
            content = self._create_xlsx_content(analysis, include_metadata)
            filename = f"{base_filename}.xlsx"
        elif format == 'json':
            content = self._create_json_content(analysis, include_metadata)
            filename = f"{base_filename}.json"
        else:  # txt
            content = self._create_txt_content(analysis, include_metadata)
            filename = f"{base_filename}.txt"
            
        return content, filename
    
    def _create_docx_content(self, analysis: AnalyseJuridique, include_metadata: bool) -> bytes:
        """Crée un document DOCX"""
        doc = Document()
        
        # Titre
        title = doc.add_heading('Analyse Juridique', 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Métadonnées
        if include_metadata:
            doc.add_paragraph(f"Date: {analysis.date_analyse.strftime('%d/%m/%Y %H:%M')}")
            doc.add_paragraph(f"Modèle: {analysis.model_used}")
            doc.add_paragraph(f"ID: {analysis.id}")
            doc.add_paragraph()
        
        # Description du cas
        doc.add_heading('Description du cas', 1)
        doc.add_paragraph(analysis.description_cas)
        
        # Qualification juridique
        doc.add_heading('Qualification juridique', 1)
        doc.add_paragraph(analysis.qualification_juridique)
        
        # Infractions identifiées
        doc.add_heading('Infractions identifiées', 1)
        for infraction in analysis.infractions_identifiees:
            doc.add_heading(infraction.nom, 2)
            doc.add_paragraph(f"Qualification: {infraction.qualification}")
            doc.add_paragraph(f"Articles: {', '.join(infraction.articles)}")
            
            # Éléments constitutifs
            doc.add_paragraph("Éléments constitutifs:")
            for element in infraction.elements_constitutifs:
                doc.add_paragraph(f"• {element}", style='List Bullet')
        
        # Régime de responsabilité
        doc.add_heading('Régime de responsabilité', 1)
        doc.add_paragraph(analysis.regime_responsabilite)
        
        # Sanctions encourues
        doc.add_heading('Sanctions encourues', 1)
        for type_sanction, details in analysis.sanctions_encourues.items():
            doc.add_paragraph(f"{type_sanction}: {details}")
        
        # Jurisprudences citées
        if analysis.jurisprudences_citees:
            doc.add_heading('Jurisprudences citées', 1)
            for juris in analysis.jurisprudences_citees:
                doc.add_paragraph(f"• {juris}", style='List Bullet')
        
        # Recommandations
        doc.add_heading('Recommandations', 1)
        for i, reco in enumerate(analysis.recommandations, 1):
            doc.add_paragraph(f"{i}. {reco}")
        
        # Niveau de risque
        doc.add_heading('Évaluation du risque', 1)
        doc.add_paragraph(f"Niveau de risque global: {analysis.niveau_risque}")
        
        # Sauvegarder en mémoire
        doc_io = io.BytesIO()
        doc.save(doc_io)
        doc_io.seek(0)
        
        return doc_io.getvalue()
    
    def _create_xlsx_content(self, analysis: AnalyseJuridique, include_metadata: bool) -> bytes:
        """Crée un fichier Excel"""
        wb = openpyxl.Workbook()
        
        # Feuille de synthèse
        ws_synthese = wb.active
        ws_synthese.title = "Synthèse"
        
        # En-têtes avec style
        headers = ['Élément', 'Valeur']
        for col, header in enumerate(headers, 1):
            cell = ws_synthese.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            cell.alignment = Alignment(horizontal="center")
        
        # Données de synthèse
        row = 2
        if include_metadata:
            ws_synthese.cell(row=row, column=1, value="Date d'analyse")
            ws_synthese.cell(row=row, column=2, value=analysis.date_analyse.strftime('%d/%m/%Y %H:%M'))
            row += 1
            
            ws_synthese.cell(row=row, column=1, value="Modèle utilisé")
            ws_synthese.cell(row=row, column=2, value=analysis.model_used)
            row += 1
        
        ws_synthese.cell(row=row, column=1, value="Niveau de risque")
        ws_synthese.cell(row=row, column=2, value=analysis.niveau_risque)
        row += 1
        
        ws_synthese.cell(row=row, column=1, value="Nombre d'infractions")
        ws_synthese.cell(row=row, column=2, value=len(analysis.infractions_identifiees))
        
        # Feuille des infractions
        ws_infractions = wb.create_sheet("Infractions")
        inf_headers = ['Infraction', 'Qualification', 'Articles', 'Prescription']
        for col, header in enumerate(inf_headers, 1):
            cell = ws_infractions.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="E7E6E6", end_color="E7E6E6", fill_type="solid")
        
        for row, infraction in enumerate(analysis.infractions_identifiees, 2):
            ws_infractions.cell(row=row, column=1, value=infraction.nom)
            ws_infractions.cell(row=row, column=2, value=infraction.qualification)
            ws_infractions.cell(row=row, column=3, value=', '.join(infraction.articles))
            ws_infractions.cell(row=row, column=4, value=infraction.prescription)
        
        # Ajuster les largeurs de colonnes
        for ws in [ws_synthese, ws_infractions]:
            for column_cells in ws.columns:
                length = max(len(str(cell.value)) for cell in column_cells if cell.value)
                ws.column_dimensions[column_cells[0].column_letter].width = min(length + 2, 50)
        
        # Sauvegarder
        excel_io = io.BytesIO()
        wb.save(excel_io)
        excel_io.seek(0)
        
        return excel_io.getvalue()
    
    def _create_json_content(self, analysis: AnalyseJuridique, include_metadata: bool) -> bytes:
        """Crée un export JSON"""
        data = {
            "description_cas": analysis.description_cas,
            "qualification_juridique": analysis.qualification_juridique,
            "infractions_identifiees": [
                {
                    "nom": inf.nom,
                    "qualification": inf.qualification,
                    "articles": inf.articles,
                    "elements_constitutifs": inf.elements_constitutifs,
                    "sanctions": inf.sanctions,
                    "prescription": inf.prescription
                }
                for inf in analysis.infractions_identifiees
            ],
            "regime_responsabilite": analysis.regime_responsabilite,
            "sanctions_encourues": analysis.sanctions_encourues,
            "jurisprudences_citees": analysis.jurisprudences_citees,
            "recommandations": analysis.recommandations,
            "niveau_risque": analysis.niveau_risque
        }
        
        if include_metadata:
            data["metadata"] = {
                "id": analysis.id,
                "date_analyse": analysis.date_analyse.isoformat(),
                "model_used": analysis.model_used
            }
        
        return json.dumps(data, indent=2, ensure_ascii=False).encode('utf-8')
    
    def _create_txt_content(self, analysis: AnalyseJuridique, include_metadata: bool) -> bytes:
        """Crée un export texte"""
        lines = []
        
        lines.append("ANALYSE JURIDIQUE")
        lines.append("=" * 50)
        lines.append("")
        
        if include_metadata:
            lines.append(f"Date: {analysis.date_analyse.strftime('%d/%m/%Y %H:%M')}")
            lines.append(f"Modèle: {analysis.model_used}")
            lines.append(f"ID: {analysis.id}")
            lines.append("")
        
        lines.append("DESCRIPTION DU CAS")
        lines.append("-" * 30)
        lines.append(analysis.description_cas)
        lines.append("")
        
        lines.append("QUALIFICATION JURIDIQUE")
        lines.append("-" * 30)
        lines.append(analysis.qualification_juridique)
        lines.append("")
        
        lines.append("INFRACTIONS IDENTIFIÉES")
        lines.append("-" * 30)
        for inf in analysis.infractions_identifiees:
            lines.append(f"\n{inf.nom}")
            lines.append(f"Qualification: {inf.qualification}")
            lines.append(f"Articles: {', '.join(inf.articles)}")
            lines.append("Éléments constitutifs:")
            for elem in inf.elements_constitutifs:
                lines.append(f"  • {elem}")
        lines.append("")
        
        lines.append("RÉGIME DE RESPONSABILITÉ")
        lines.append("-" * 30)
        lines.append(analysis.regime_responsabilite)
        lines.append("")
        
        lines.append("SANCTIONS ENCOURUES")
        lines.append("-" * 30)
        for type_s, details in analysis.sanctions_encourues.items():
            lines.append(f"{type_s}: {details}")
        lines.append("")
        
        if analysis.jurisprudences_citees:
            lines.append("JURISPRUDENCES CITÉES")
            lines.append("-" * 30)
            for juris in analysis.jurisprudences_citees:
                lines.append(f"• {juris}")
            lines.append("")
        
        lines.append("RECOMMANDATIONS")
        lines.append("-" * 30)
        for i, reco in enumerate(analysis.recommandations, 1):
            lines.append(f"{i}. {reco}")
        lines.append("")
        
        lines.append("NIVEAU DE RISQUE")
        lines.append("-" * 30)
        lines.append(f"Risque global: {analysis.niveau_risque}")
        
        return '\n'.join(lines).encode('utf-8')
    
    def _create_pdf_content(self, analysis: AnalyseJuridique, include_metadata: bool) -> bytes:
        """
        Crée un PDF (version simplifiée - pour un vrai PDF, utiliser reportlab)
        Pour l'instant, on retourne le contenu texte qui peut être converti en PDF
        """
        # Dans une vraie implémentation, utiliser reportlab ou weasyprint
        # Pour l'instant, on retourne le contenu texte
        return self._create_txt_content(analysis, include_metadata)
    
    def batch_import(self, files: List) -> Dict[str, Any]:
        """Import en lot de plusieurs documents"""
        results = {
            'success': [],
            'failed': [],
            'total_content': ""
        }
        
        for file in files:
            success, content, message = self.import_document(file)
            
            if success:
                results['success'].append({
                    'filename': file.name,
                    'message': message,
                    'content_length': len(content)
                })
                results['total_content'] += f"\n\n--- {file.name} ---\n{content}"
            else:
                results['failed'].append({
                    'filename': file.name,
                    'error': message
                })
        
        return results
    
    def create_download_link(self, content: bytes, filename: str, text: str) -> str:
        """Crée un lien de téléchargement pour Streamlit"""
        b64 = base64.b64encode(content).decode()
        return f'<a href="data:application/octet-stream;base64,{b64}" download="{filename}">{text}</a>'
    
    def get_import_stats(self) -> Dict[str, Any]:
        """Retourne des statistiques sur les imports"""
        if not self.imported_documents:
            return {'count': 0}
            
        return {
            'count': len(self.imported_documents),
            'total_size': sum(doc['size'] for doc in self.imported_documents),
            'types': pd.Series([Path(doc['filename']).suffix for doc in self.imported_documents]).value_counts().to_dict(),
            'latest': self.imported_documents[-1]['filename'] if self.imported_documents else None
        }


# Fonctions d'interface Streamlit
def display_import_interface():
    """Interface d'import de documents"""
    st.markdown("### 📤 Import de documents")
    
    # Options d'import
    col1, col2 = st.columns([3, 1])
    
    with col1:
        uploaded_files = st.file_uploader(
            "Sélectionnez un ou plusieurs fichiers",
            type=['pdf', 'docx', 'txt', 'json', 'xlsx', 'csv'],
            accept_multiple_files=True,
            help="Formats supportés: PDF, DOCX, TXT, JSON, XLSX, CSV"
        )
    
    with col2:
        process_option = st.radio(
            "Traitement",
            ["Individuel", "Fusionné"],
            help="Individuel: chaque fichier séparément\nFusionné: combiner tous les fichiers"
        )
    
    if uploaded_files:
        doc_manager = st.session_state.get('doc_manager', DocumentManager())
        
        if st.button("🚀 Importer", type="primary"):
            with st.spinner("Import en cours..."):
                if process_option == "Fusionné":
                    results = doc_manager.batch_import(uploaded_files)
                    
                    # Afficher les résultats
                    if results['success']:
                        st.success(f"✅ {len(results['success'])} fichiers importés avec succès")
                        
                        # Afficher le contenu fusionné
                        with st.expander("Contenu importé", expanded=True):
                            st.text_area(
                                "Texte extrait",
                                value=results['total_content'],
                                height=400
                            )
                            
                        # Stocker dans session_state
                        st.session_state['imported_content'] = results['total_content']
                    
                    if results['failed']:
                        st.error(f"❌ {len(results['failed'])} échecs")
                        for fail in results['failed']:
                            st.caption(f"- {fail['filename']}: {fail['error']}")
                else:
                    # Import individuel
                    for file in uploaded_files:
                        success, content, message = doc_manager.import_document(file)
                        
                        if success:
                            st.success(f"✅ {message}")
                            with st.expander(f"Contenu de {file.name}"):
                                st.text_area(
                                    "Texte extrait",
                                    value=content[:1000] + "..." if len(content) > 1000 else content,
                                    height=200,
                                    key=f"content_{file.name}"
                                )
                        else:
                            st.error(f"❌ {message}")
        
        # Statistiques
        if 'doc_manager' in st.session_state:
            stats = doc_manager.get_import_stats()
            if stats['count'] > 0:
                st.info(f"📊 {stats['count']} documents importés au total")

def display_export_interface(analysis: Optional[AnalyseJuridique] = None):
    """Interface d'export de documents"""
    if not analysis:
        st.warning("Aucune analyse à exporter")
        return
        
    st.markdown("### 💾 Export de l'analyse")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        format = st.selectbox(
            "Format d'export",
            options=['docx', 'xlsx', 'json', 'txt', 'pdf'],
            help="Sélectionnez le format de sortie"
        )
    
    with col2:
        include_metadata = st.checkbox(
            "Inclure métadonnées",
            value=True,
            help="Date, modèle utilisé, etc."
        )
    
    with col3:
        if st.button("📥 Générer export", type="primary"):
            doc_manager = st.session_state.get('doc_manager', DocumentManager())
            
            with st.spinner("Génération en cours..."):
                content, filename = doc_manager.export_analysis(
                    analysis,
                    format,
                    include_metadata
                )
                
                # Créer le bouton de téléchargement
                st.download_button(
                    label=f"⬇️ Télécharger {filename}",
                    data=content,
                    file_name=filename,
                    mime="application/octet-stream"
                )
                
                st.success(f"Export '{filename}' prêt !")

# Export
__all__ = [
    'DocumentManager',
    'display_import_interface',
    'display_export_interface'
]