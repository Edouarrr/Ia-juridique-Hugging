"""Module d'export de documents"""

import streamlit as st
from datetime import datetime
import io
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    import docx
    from docx.shared import Pt, Inches, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
    from docx.enum.style import WD_STYLE_TYPE
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

def process_export_request(query: str, analysis: dict):
    """Traite une demande d'export"""
    
    format = analysis.get('format', 'docx')
    
    # Déterminer ce qu'il faut exporter
    content_to_export = None
    filename_base = "export"
    
    # Priorité : rédaction > analyse > recherche
    if st.session_state.get('redaction_result'):
        content_to_export = st.session_state.redaction_result['document']
        filename_base = f"{st.session_state.redaction_result['type']}"
    
    elif st.session_state.get('ai_analysis_results'):
        content_to_export = format_ai_analysis_for_export(st.session_state.ai_analysis_results)
        filename_base = "analyse"
    
    elif st.session_state.get('search_results'):
        content_to_export = format_search_results_for_export(st.session_state.search_results)
        filename_base = "recherche"
    
    else:
        st.warning("⚠️ Aucun contenu à exporter")
        return
    
    # Exporter selon le format
    export_functions = {
        'docx': export_to_docx,
        'pdf': export_to_pdf,
        'txt': export_to_txt,
        'html': export_to_html,
        'xlsx': export_to_xlsx
    }
    
    export_func = export_functions.get(format, export_to_txt)
    
    try:
        exported_data = export_func(content_to_export, analysis)
        
        # Créer le bouton de téléchargement
        st.download_button(
            f"💾 Télécharger {format.upper()}",
            exported_data,
            f"{filename_base}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}",
            get_mime_type(format),
            key=f"download_export_{format}"
        )
        
        st.success(f"✅ Export {format.upper()} prêt")
        
    except Exception as e:
        st.error(f"❌ Erreur export: {str(e)}")

def create_formatted_docx(content: str, doc_type: str) -> bytes:
    """Crée un document Word avec mise en forme professionnelle"""
    
    if not DOCX_AVAILABLE:
        return content.encode('utf-8')
    
    try:
        doc = docx.Document()
        
        # Configuration des marges
        sections = doc.sections
        for section in sections:
            section.top_margin = Inches(1)
            section.bottom_margin = Inches(1)
            section.left_margin = Inches(1.5)
            section.right_margin = Inches(1)
        
        # Styles personnalisés
        styles = doc.styles
        
        # Style titre
        title_style = styles.add_style('JuridicalTitle', WD_STYLE_TYPE.PARAGRAPH)
        title_style.font.name = 'Times New Roman'
        title_style.font.size = Pt(16)
        title_style.font.bold = True
        title_style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title_style.paragraph_format.space_after = Pt(24)
        
        # Analyser et formater le contenu
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            
            if not line:
                doc.add_paragraph()
                continue
            
            # Titre principal
            if line.isupper() and len(line.split()) < 10:
                p = doc.add_paragraph(line, style='JuridicalTitle')
            
            # Sections principales
            elif line.startswith(('I.', 'II.', 'III.', 'IV.', 'V.')):
                p = doc.add_paragraph(line)
                p.style.font.bold = True
                p.style.font.size = Pt(14)
            
            # Sous-sections
            elif line.startswith(('A.', 'B.', 'C.', 'D.')):
                p = doc.add_paragraph(line)
                p.style.font.bold = True
                p.style.font.size = Pt(13)
            
            # Points
            elif line.startswith('-'):
                doc.add_paragraph(line[1:].strip(), style='List Bullet')
            
            # Texte normal
            else:
                p = doc.add_paragraph(line)
                p.style.font.name = 'Times New Roman'
                p.style.font.size = Pt(12)
        
        # Pied de page
        section = doc.sections[0]
        footer = section.footer
        footer_para = footer.paragraphs[0]
        footer_para.text = f"Document généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')} - {doc_type.title()}"
        footer_para.style.font.size = Pt(9)
        footer_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Sauvegarder
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        
        return buffer.getvalue()
        
    except Exception as e:
        st.error(f"Erreur création document Word: {e}")
        return content.encode('utf-8')

def export_to_pdf(content: str, analysis: dict) -> bytes:
    """Exporte vers PDF"""
    st.warning("⚠️ Export PDF nécessite l'installation de bibliothèques supplémentaires")
    return content.encode('utf-8')

def export_to_txt(content: str, analysis: dict) -> bytes:
    """Exporte en texte brut"""
    return content.encode('utf-8')

def export_to_html(content: str, analysis: dict) -> bytes:
    """Exporte vers HTML avec style"""
    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>{analysis.get('document_type', 'Document').title()}</title>
    <style>
        body {{ font-family: 'Times New Roman', serif; margin: 40px; }}
        h1 {{ text-align: center; color: #2c3e50; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        p {{ text-align: justify; line-height: 1.6; }}
    </style>
</head>
<body>
    <h1>{analysis.get('document_type', 'Document').upper()}</h1>
    <div class="content">
        {content.replace(chr(10), '<br>')}
    </div>
</body>
</html>"""
    
    return html.encode('utf-8')

def export_to_xlsx(content: str, analysis: dict) -> bytes:
    """Exporte vers Excel"""
    if not PANDAS_AVAILABLE:
        st.error("❌ pandas requis pour l'export Excel")
        return content.encode('utf-8')
    
    try:
        # Créer un DataFrame
        lines = content.split('\n')
        df = pd.DataFrame({'Contenu': lines})
        
        # Exporter
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Données', index=False)
        
        buffer.seek(0)
        return buffer.getvalue()
        
    except Exception as e:
        st.error(f"Erreur export Excel: {e}")
        return content.encode('utf-8')

def get_mime_type(format: str) -> str:
    """Retourne le type MIME pour un format"""
    mime_types = {
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'pdf': 'application/pdf',
        'txt': 'text/plain',
        'html': 'text/html',
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    }
    return mime_types.get(format, 'application/octet-stream')

def format_ai_analysis_for_export(analysis_results: dict) -> str:
    """Formate les résultats d'analyse IA pour l'export"""
    content = f"ANALYSE IA - {analysis_results.get('type', 'Générale').upper()}\n"
    content += f"Date : {analysis_results.get('timestamp', datetime.now()).strftime('%d/%m/%Y %H:%M')}\n"
    content += f"Documents analysés : {analysis_results.get('document_count', 0)}\n\n"
    
    if analysis_results.get('query'):
        content += f"QUESTION : {analysis_results['query']}\n\n"
    
    content += "ANALYSE :\n"
    content += analysis_results.get('content', 'Aucun contenu')
    
    return content

def format_search_results_for_export(search_results: list) -> str:
    """Formate les résultats de recherche pour l'export"""
    content = f"RÉSULTATS DE RECHERCHE\n"
    content += f"Date : {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
    content += f"Nombre de résultats : {len(search_results)}\n\n"
    
    for i, result in enumerate(search_results, 1):
        content += f"{i}. {result.get('title', 'Sans titre')}\n"
        content += f"   Source : {result.get('source', 'N/A')}\n"
        content += f"   Score : {result.get('score', 0):.2%}\n\n"
    
    return content