# managers/style_analyzer.py
"""Analyseur de style pour documents juridiques"""

import re
import io
import logging
from typing import Dict, List, Set, Optional, Any
from collections import defaultdict, Counter
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from docx import Document as DocxDocument
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    logger.warning("Module python-docx non disponible")

from models.dataclasses import Document, StylePattern

class StyleAnalyzer:
    """Analyse et apprend le style de rédaction des documents"""
    
    def __init__(self):
        self.patterns = defaultdict(list)
        self.formules_types = defaultdict(set)
        self.structures = defaultdict(list)
    
    def analyze_document(self, document: Document, type_acte: str) -> StylePattern:
        """Analyse un document pour en extraire le style"""
        content = document.content
        
        # Analyser la structure
        structure = self._extract_structure(content)
        
        # Extraire les formules types
        formules = self._extract_formules(content)
        
        # Analyser la mise en forme
        mise_en_forme = self._analyze_formatting(content)
        
        # Analyser le vocabulaire
        vocabulaire = self._analyze_vocabulary(content)
        
        # Extraire des paragraphes types
        paragraphes_types = self._extract_sample_paragraphs(content)
        
        pattern = StylePattern(
            document_id=document.id,
            type_acte=type_acte,
            structure=structure,
            formules=list(formules),
            mise_en_forme=mise_en_forme,
            vocabulaire=vocabulaire,
            paragraphes_types=paragraphes_types
        )
        
        # Stocker le pattern
        self.patterns[type_acte].append(pattern)
        
        return pattern
    
    def analyze_word_document(self, doc_bytes: bytes, type_acte: str) -> Optional[StylePattern]:
        """Analyse un document Word pour en extraire le style"""
        if not DOCX_AVAILABLE:
            return None
        
        try:
            doc = DocxDocument(io.BytesIO(doc_bytes))
            
            # Extraire le contenu et la structure
            content = []
            structure = {
                'sections': [],
                'styles_utilises': set(),
                'mise_en_forme_paragraphes': []
            }
            
            for paragraph in doc.paragraphs:
                text = paragraph.text.strip()
                if text:
                    content.append(text)
                    
                    # Analyser le style du paragraphe
                    para_style = {
                        'style': paragraph.style.name if paragraph.style else 'Normal',
                        'alignment': str(paragraph.alignment) if paragraph.alignment else 'LEFT',
                        'first_line_indent': paragraph.paragraph_format.first_line_indent,
                        'left_indent': paragraph.paragraph_format.left_indent,
                        'right_indent': paragraph.paragraph_format.right_indent,
                        'space_before': paragraph.paragraph_format.space_before,
                        'space_after': paragraph.paragraph_format.space_after,
                        'line_spacing': paragraph.paragraph_format.line_spacing
                    }
                    
                    structure['mise_en_forme_paragraphes'].append(para_style)
                    
                    if paragraph.style:
                        structure['styles_utilises'].add(paragraph.style.name)
                    
                    # Détecter les sections
                    if paragraph.style and 'Heading' in paragraph.style.name:
                        structure['sections'].append({
                            'titre': text,
                            'niveau': paragraph.style.name
                        })
            
            # Créer un document temporaire pour l'analyse
            temp_doc = Document(
                id=f"word_doc_{datetime.now().timestamp()}",
                title=type_acte,
                content='\n'.join(content),
                source='word'
            )
            
            # Analyser avec la méthode standard
            pattern = self.analyze_document(temp_doc, type_acte)
            
            # Enrichir avec les informations Word spécifiques
            pattern.structure.update({
                'word_styles': list(structure['styles_utilises']),
                'word_formatting': structure['mise_en_forme_paragraphes'][:10]
            })
            
            return pattern
            
        except Exception as e:
            logger.error(f"Erreur analyse document Word: {e}")
            return None
    
    def _extract_structure(self, content: str) -> Dict[str, Any]:
        """Extrait la structure du document"""
        lines = content.split('\n')
        structure = {
            'sections': [],
            'niveau_hierarchie': 0,
            'longueur_sections': []
        }
        
        current_section = None
        section_content = []
        
        for line in lines:
            if self._is_title(line):
                if current_section:
                    structure['sections'].append({
                        'titre': current_section,
                        'longueur': len(section_content)
                    })
                    structure['longueur_sections'].append(len(section_content))
                
                current_section = line.strip()
                section_content = []
            else:
                section_content.append(line)
        
        if current_section:
            structure['sections'].append({
                'titre': current_section,
                'longueur': len(section_content)
            })
        
        return structure
    
    def _extract_formules(self, content: str) -> Set[str]:
        """Extrait les formules types du document"""
        formules = set()
        
        patterns = [
            r"J'ai l'honneur de.*?[.!]",
            r"Il résulte de.*?[.!]",
            r"Aux termes de.*?[.!]",
            r"En l'espèce.*?[.!]",
            r"Par ces motifs.*?[.!]",
            r"Il convient de.*?[.!]",
            r"Force est de constater.*?[.!]",
            r"Il apparaît que.*?[.!]",
            r"Attendu que.*?[.!]",
            r"Considérant que.*?[.!]",
            r"Je vous prie d'agréer.*?[.!]",
            r"Veuillez agréer.*?[.!]",
            r"Dans l'attente de.*?[.!]",
            r"Je reste à votre disposition.*?[.!]"
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE | re.DOTALL)
            for match in matches:
                formule = match.group(0).strip()
                if len(formule) < 200:
                    formules.add(formule)
        
        return formules
    
    def _analyze_formatting(self, content: str) -> Dict[str, Any]:
        """Analyse la mise en forme du document"""
        return {
            'longueur_moyenne_paragraphe': self._avg_paragraph_length(content),
            'utilise_tirets': '-' in content,
            'utilise_numerotation': bool(re.search(r'\d+\.', content)),
            'utilise_majuscules_titres': bool(re.search(r'^[A-Z\s]+$', content, re.MULTILINE)),
            'espacement_sections': content.count('\n\n')
        }
    
    def _analyze_vocabulary(self, content: str) -> Dict[str, int]:
        """Analyse le vocabulaire utilisé"""
        words = re.findall(r'\b[a-zA-ZÀ-ÿ]+\b', content.lower())
        
        word_freq = defaultdict(int)
        for word in words:
            if len(word) > 3:
                word_freq[word] += 1
        
        return dict(sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:100])
    
    def _extract_sample_paragraphs(self, content: str) -> List[str]:
        """Extrait des paragraphes types"""
        paragraphs = content.split('\n\n')
        
        samples = []
        for para in paragraphs:
            if 50 < len(para) < 500:
                samples.append(para.strip())
        
        return samples[:10]
    
    def _is_title(self, line: str) -> bool:
        """Détermine si une ligne est un titre"""
        line = line.strip()
        
        if not line:
            return False
        
        if line.isupper() and len(line) > 3:
            return True
        
        if re.match(r'^[IVX]+\.?\s+', line):
            return True
        
        if re.match(r'^\d+\.?\s+', line):
            return True
        
        if re.match(r'^[A-Z]\.\s+', line):
            return True
        
        return False
    
    def _avg_paragraph_length(self, content: str) -> int:
        """Calcule la longueur moyenne des paragraphes"""
        paragraphs = content.split('\n\n')
        lengths = [len(p) for p in paragraphs if p.strip()]
        
        return sum(lengths) // len(lengths) if lengths else 0
    
    def generate_with_style(self, type_acte: str, contenu_base: str) -> str:
        """Génère du contenu en appliquant le style appris"""
        if type_acte not in self.patterns:
            return contenu_base
        
        patterns = self.patterns[type_acte]
        if not patterns:
            return contenu_base
        
        pattern = patterns[0]
        
        styled_content = self._apply_structure(contenu_base, pattern.structure)
        styled_content = self._insert_formules(styled_content, pattern.formules)
        styled_content = self._apply_formatting(styled_content, pattern.mise_en_forme)
        
        return styled_content
    
    def _apply_structure(self, content: str, structure: Dict[str, Any]) -> str:
        """Applique une structure au contenu"""
        sections = structure.get('sections', [])
        
        if not sections:
            return content
        
        lines = content.split('\n')
        structured = []
        
        section_size = len(lines) // len(sections) if sections else len(lines)
        
        for i, section in enumerate(sections):
            structured.append(f"\n{section['titre']}\n")
            
            start = i * section_size
            end = start + section_size if i < len(sections) - 1 else len(lines)
            
            structured.extend(lines[start:end])
        
        return '\n'.join(structured)
    
    def _insert_formules(self, content: str, formules: List[str]) -> str:
        """Insère des formules types dans le contenu"""
        if not formules:
            return content
        
        paragraphs = content.split('\n\n')
        
        for i in range(0, len(paragraphs), 3):
            if i < len(paragraphs) and formules:
                formule = formules[i % len(formules)]
                paragraphs[i] = f"{formule} {paragraphs[i]}"
        
        return '\n\n'.join(paragraphs)
    
    def _apply_formatting(self, content: str, formatting: Dict[str, Any]) -> str:
        """Applique la mise en forme au contenu"""
        if formatting.get('espacement_sections', 0) > 1:
            content = re.sub(r'\n{2,}', '\n\n\n', content)
        
        if formatting.get('utilise_numerotation'):
            lines = content.split('\n')
            numbered_lines = []
            counter = 1
            
            for line in lines:
                if line.strip() and not self._is_title(line):
                    numbered_lines.append(f"{counter}. {line}")
                    counter += 1
                else:
                    numbered_lines.append(line)
            
            content = '\n'.join(numbered_lines)
        
        return content