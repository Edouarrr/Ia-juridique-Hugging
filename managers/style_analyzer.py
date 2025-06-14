# managers/style_analyzer.py
"""Analyseur de style pour documents juridiques avec apprentissage"""

import json
import re
import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st

from modules.dataclasses import Document, StyleLearningResult, StylePattern


class StyleAnalyzer:
    """Analyse et apprend le style des documents juridiques"""
    
    def __init__(self):
        # Patterns de reconnaissance
        self.sentence_endings = re.compile(r'[.!?]+')
        self.paragraph_pattern = re.compile(r'\n\n+')
        self.numbering_patterns = {
            'roman': re.compile(r'^[IVXLCDM]+\.?\s'),
            'letter': re.compile(r'^[A-Z]\.?\s'),
            'number': re.compile(r'^\d+\.?\s'),
            'dash': re.compile(r'^-\s'),
            'bullet': re.compile(r'^[•·]\s')
        }
        
        # Stockage des styles appris
        if 'learned_styles' not in st.session_state:
            st.session_state.learned_styles = {}
    
    def analyze_document(self, document: Document) -> StylePattern:
        """Analyse complète du style d'un document"""
        content = document.content
        
        # Extraire la structure
        structure = self._extract_structure(content)
        
        # Extraire les formules types
        formules = self._extract_formules(content)
        
        # Analyser la mise en forme
        mise_en_forme = self._analyze_formatting(content)
        
        # Analyser le vocabulaire
        vocabulaire = self._analyze_vocabulary(content)
        
        # Extraire les paragraphes types
        paragraphes_types = self._extract_typical_paragraphs(content)
        
        # Analyser la numérotation
        numerotation = self._analyze_numbering(content)
        
        # Analyser les formalités
        formalite = self._analyze_formality(content)
        
        # Analyser l'argumentation
        argumentation = self._analyze_argumentation(content)
        
        return StylePattern(
            document_id=document.id,
            type_acte=document.type,
            structure=structure,
            formules=formules,
            mise_en_forme=mise_en_forme,
            vocabulaire=vocabulaire,
            paragraphes_types=paragraphes_types,
            numerotation=numerotation,
            formalite=formalite,
            argumentation=argumentation
        )
    
    def _extract_structure(self, content: str) -> Dict[str, Any]:
        """Extrait la structure du document"""
        # Identifier les sections principales
        section_patterns = [
            r'^[IVX]+\.?\s+[A-Z\s]+$',  # Sections numérotées en romain
            r'^[A-Z][A-Z\s]+:$',         # Sections en majuscules avec :
            r'^#{1,3}\s+.+$',            # Markdown headers
            r'^\d+\.\s+[A-Z].+$'         # Sections numérotées
        ]
        
        sections = []
        for pattern in section_patterns:
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                sections.append({
                    'text': match.group().strip(),
                    'position': match.start(),
                    'type': 'section'
                })
        
        # Trier par position
        sections.sort(key=lambda x: x['position'])
        
        return {
            'sections': sections,
            'section_count': len(sections),
            'has_numbered_sections': any('roman' in self._identify_numbering(s['text']) 
                                       for s in sections)
        }
    
    def _extract_formules(self, content: str) -> List[str]:
        """Extrait les formules juridiques types"""
        formules = []
        
        # Patterns de formules courantes
        formule_patterns = [
            r'PAR CES MOTIFS[^.]*',
            r'PLAISE AU TRIBUNAL[^.]*',
            r'IL EST DEMANDÉ[^.]*',
            r'POUR CES RAISONS[^.]*',
            r'EN CONSÉQUENCE[^.]*',
            r'Ayant pour avocat[^.]*',
            r'Élisant domicile[^.]*',
            r'Sous toutes réserves[^.]*',
            r'À LA REQUÊTE DE[^.]*',
            r'J\'AI[^.]*HUISSIER[^.]*'
        ]
        
        for pattern in formule_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                formule = match.group().strip()
                if formule and len(formule) < 200:  # Éviter les trop longues
                    formules.append(formule)
        
        return list(set(formules))  # Éliminer les doublons
    
    def _analyze_formatting(self, content: str) -> Dict[str, Any]:
        """Analyse la mise en forme du document"""
        # Compter les paragraphes
        paragraphs = [p.strip() for p in self.paragraph_pattern.split(content) if p.strip()]
        
        # Analyser la longueur des phrases
        sentences = self.sentence_endings.split(content)
        sentence_lengths = [len(s.split()) for s in sentences if s.strip()]
        
        # Analyser l'utilisation des majuscules
        uppercase_lines = len(re.findall(r'^[A-Z\s]+$', content, re.MULTILINE))
        
        return {
            'paragraph_count': len(paragraphs),
            'average_paragraph_length': statistics.mean([len(p.split()) for p in paragraphs]) if paragraphs else 0,
            'sentence_count': len(sentences),
            'average_sentence_length': statistics.mean(sentence_lengths) if sentence_lengths else 0,
            'uppercase_lines': uppercase_lines,
            'uses_bold': '**' in content or '__' in content,
            'uses_italic': '*' in content or '_' in content,
            'line_breaks': content.count('\n')
        }
    
    def _analyze_vocabulary(self, content: str) -> Dict[str, Any]:
        """Analyse le vocabulaire utilisé"""
        # Nettoyer le texte
        words = re.findall(r'\b[a-zA-ZÀ-ÿ]+\b', content.lower())
        
        # Compter les mots
        word_freq = Counter(words)
        
        # Identifier les mots juridiques courants
        legal_terms = [
            'attendu', 'considérant', 'motifs', 'demande', 'défendeur',
            'tribunal', 'juridiction', 'procédure', 'instance', 'appel',
            'cassation', 'pourvoi', 'moyen', 'grief', 'violation',
            'préjudice', 'dommages', 'intérêts', 'condamner', 'débouter'
        ]
        
        legal_count = sum(word_freq.get(term, 0) for term in legal_terms)
        
        # Identifier les connecteurs logiques
        connectors = [
            'donc', 'ainsi', 'par conséquent', 'en conséquence',
            'néanmoins', 'toutefois', 'cependant', 'or', 'en effet',
            'par ailleurs', 'en outre', 'subsidiairement'
        ]
        
        connector_count = sum(1 for word in words if word in connectors)
        
        return {
            'total_words': len(words),
            'unique_words': len(set(words)),
            'legal_term_ratio': legal_count / len(words) if words else 0,
            'connector_ratio': connector_count / len(words) if words else 0,
            'most_common': word_freq.most_common(20),
            'vocabulary_richness': len(set(words)) / len(words) if words else 0
        }
    
    def _extract_typical_paragraphs(self, content: str) -> List[str]:
        """Extrait les paragraphes types représentatifs"""
        paragraphs = [p.strip() for p in self.paragraph_pattern.split(content) if p.strip()]
        
        # Filtrer les paragraphes intéressants
        typical = []
        for para in paragraphs:
            # Paragraphes avec formules juridiques
            if any(phrase in para.upper() for phrase in ['ATTENDU QUE', 'CONSIDÉRANT', 'PAR CES MOTIFS']):
                typical.append(para)
            # Paragraphes de transition
            elif any(word in para.lower() for word in ['en conséquence', 'par ailleurs', 'subsidiairement']):
                typical.append(para)
        
        return typical[:10]  # Limiter à 10 paragraphes
    
    def _analyze_numbering(self, content: str) -> Dict[str, Any]:
        """Analyse le système de numérotation"""
        numbering_found = defaultdict(int)
        
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            for num_type, pattern in self.numbering_patterns.items():
                if pattern.match(line):
                    numbering_found[num_type] += 1
        
        # Déterminer le style dominant
        if numbering_found:
            dominant = max(numbering_found, key=numbering_found.get)
        else:
            dominant = 'none'
        
        return {
            'dominant_style': dominant,
            'styles_found': dict(numbering_found),
            'total_numbered': sum(numbering_found.values())
        }
    
    def _analyze_formality(self, content: str) -> Dict[str, Any]:
        """Analyse le niveau de formalité"""
        # Indicateurs de formalité
        formal_indicators = {
            'vouvoiement': len(re.findall(r'\b(vous|votre|vos)\b', content, re.IGNORECASE)),
            'formules_politesse': len(re.findall(r'(veuillez|agréer|sentiments|considération)', content, re.IGNORECASE)),
            'subjonctif': len(re.findall(r'(qu\'il soit|qu\'elle soit|puisse|fasse)', content, re.IGNORECASE)),
            'conditionnel': len(re.findall(r'(serait|pourrait|devrait|conviendrait)', content, re.IGNORECASE))
        }
        
        # Score de formalité
        total_words = len(content.split())
        formality_score = sum(formal_indicators.values()) / total_words if total_words else 0
        
        return {
            'indicators': formal_indicators,
            'formality_score': formality_score,
            'level': 'très formel' if formality_score > 0.05 else 'formel' if formality_score > 0.02 else 'standard'
        }
    
    def _analyze_argumentation(self, content: str) -> Dict[str, List[str]]:
        """Analyse la structure argumentative"""
        argumentation = {
            'introductions': [],
            'developpements': [],
            'conclusions': []
        }
        
        # Patterns d'introduction d'arguments
        intro_patterns = [
            r'Il convient de rappeler que[^.]+\.',
            r'Il résulte de[^.]+\.',
            r'Il est constant que[^.]+\.',
            r'Force est de constater que[^.]+\.'
        ]
        
        # Patterns de développement
        dev_patterns = [
            r'En effet[^.]+\.',
            r'Par ailleurs[^.]+\.',
            r'En outre[^.]+\.',
            r'De plus[^.]+\.'
        ]
        
        # Patterns de conclusion
        concl_patterns = [
            r'En conséquence[^.]+\.',
            r'Par conséquent[^.]+\.',
            r'Ainsi[^.]+\.',
            r'Il s\'ensuit que[^.]+\.'
        ]
        
        # Extraire les arguments
        for patterns, category in [(intro_patterns, 'introductions'),
                                  (dev_patterns, 'developpements'),
                                  (concl_patterns, 'conclusions')]:
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    argumentation[category].append(match.group().strip())
        
        return argumentation
    
    def _identify_numbering(self, text: str) -> str:
        """Identifie le type de numérotation d'un texte"""
        for num_type, pattern in self.numbering_patterns.items():
            if pattern.match(text.strip()):
                return num_type
        return 'none'
    
    def learn_style(self, documents: List[Document], style_name: str) -> StyleLearningResult:
        """Apprend un style à partir de plusieurs documents"""
        if not documents:
            return StyleLearningResult(
                style_name=style_name,
                documents_analyzed=0,
                confidence_score=0.0
            )
        
        # Analyser tous les documents
        patterns = []
        for doc in documents:
            pattern = self.analyze_document(doc)
            patterns.append(pattern)
        
        # Agréger les résultats
        result = self._aggregate_patterns(patterns, style_name)
        
        # Sauvegarder le style appris
        st.session_state.learned_styles[style_name] = result
        
        return result
    
    def _aggregate_patterns(self, patterns: List[StylePattern], style_name: str) -> StyleLearningResult:
        """Agrège plusieurs patterns pour créer un style"""
        if not patterns:
            return StyleLearningResult(style_name=style_name, documents_analyzed=0)
        
        # Collecter toutes les données
        all_formules = []
        all_sentence_lengths = []
        all_paragraph_lengths = []
        all_transitions = []
        all_arguments = []
        all_citations = []
        
        for pattern in patterns:
            all_formules.extend(pattern.formules)
            
            if 'average_sentence_length' in pattern.mise_en_forme:
                all_sentence_lengths.append(pattern.mise_en_forme['average_sentence_length'])
            
            if 'average_paragraph_length' in pattern.mise_en_forme:
                all_paragraph_lengths.append(pattern.mise_en_forme['average_paragraph_length'])
            
            # Extraire les transitions
            for arg_list in pattern.argumentation.values():
                for arg in arg_list:
                    # Identifier les mots de transition
                    transitions = re.findall(r'(En effet|Par ailleurs|En outre|De plus|En conséquence|Ainsi)', arg)
                    all_transitions.extend(transitions)
        
        # Calculer les statistiques
        result = StyleLearningResult(
            style_name=style_name,
            documents_analyzed=len(patterns),
            confidence_score=min(1.0, len(patterns) / 10),  # Confiance basée sur le nombre de docs
            average_sentence_length=int(statistics.mean(all_sentence_lengths)) if all_sentence_lengths else 0,
            average_paragraph_length=int(statistics.mean(all_paragraph_lengths)) if all_paragraph_lengths else 0,
            common_phrases=list(Counter(all_formules).most_common(10)),
            transition_words=list(Counter(all_transitions).most_common(10)),
            argument_patterns=self._extract_argument_patterns(patterns),
            citation_patterns=self._extract_citation_patterns(patterns),
            paragraph_numbering_style=self._determine_numbering_style(patterns)
        )
        
        return result
    
    def _extract_argument_patterns(self, patterns: List[StylePattern]) -> List[str]:
        """Extrait les patterns d'argumentation communs"""
        all_args = []
        for pattern in patterns:
            for args in pattern.argumentation.values():
                all_args.extend(args)
        
        # Identifier les structures récurrentes
        # Simplification : retourner les débuts de phrases les plus fréquents
        beginnings = []
        for arg in all_args:
            words = arg.split()[:5]  # Premiers 5 mots
            if words:
                beginnings.append(' '.join(words))
        
        return [b[0] for b in Counter(beginnings).most_common(5)]
    
    def _extract_citation_patterns(self, patterns: List[StylePattern]) -> List[str]:
        """Extrait les patterns de citation"""
        citation_patterns = [
            r'(Cass\.\s+\w+\.?,?\s+\d+\s+\w+\s+\d{4})',
            r'(CA\s+\w+,?\s+\d+\s+\w+\s+\d{4})',
            r'(Article\s+\d+)',
            r'(aux termes de)',
            r'(conformément à)'
        ]
        
        found_patterns = []
        for pattern in patterns:
            content = ' '.join(pattern.formules + pattern.paragraphes_types)
            for cit_pattern in citation_patterns:
                if re.search(cit_pattern, content, re.IGNORECASE):
                    found_patterns.append(cit_pattern)
        
        return list(set(found_patterns))[:5]
    
    def _determine_numbering_style(self, patterns: List[StylePattern]) -> Optional[str]:
        """Détermine le style de numérotation dominant"""
        all_styles = []
        for pattern in patterns:
            if pattern.numerotation and 'dominant_style' in pattern.numerotation:
                all_styles.append(pattern.numerotation['dominant_style'])
        
        if all_styles:
            counter = Counter(all_styles)
            return counter.most_common(1)[0][0]
        
        return None
    
    def apply_style(self, content: str, style_name: str) -> str:
        """Applique un style appris à un contenu"""
        if style_name not in st.session_state.learned_styles:
            return content  # Pas de style appris
        
        style = st.session_state.learned_styles[style_name]
        
        # Appliquer les transformations basiques
        # (Cette méthode pourrait être beaucoup plus sophistiquée)
        
        # Remplacer les transitions génériques par celles du style
        if style.transition_words:
            generic_transitions = ['De plus', 'En outre', 'Par ailleurs']
            style_transitions = [t[0] for t in style.transition_words[:3]]
            
            for i, generic in enumerate(generic_transitions):
                if i < len(style_transitions):
                    content = content.replace(generic, style_transitions[i])
        
        return content
    
    def compare_styles(self, style1: str, style2: str) -> Dict[str, Any]:
        """Compare deux styles appris"""
        if style1 not in st.session_state.learned_styles:
            return {'error': f"Style '{style1}' non trouvé"}
        if style2 not in st.session_state.learned_styles:
            return {'error': f"Style '{style2}' non trouvé"}
        
        s1 = st.session_state.learned_styles[style1]
        s2 = st.session_state.learned_styles[style2]
        
        return {
            'sentence_length_diff': abs(s1.average_sentence_length - s2.average_sentence_length),
            'paragraph_length_diff': abs(s1.average_paragraph_length - s2.average_paragraph_length),
            'common_phrases_overlap': len(set(p[0] for p in s1.common_phrases) & 
                                        set(p[0] for p in s2.common_phrases)),
            'transition_similarity': len(set(t[0] for t in s1.transition_words) & 
                                       set(t[0] for t in s2.transition_words)),
            'numbering_match': s1.paragraph_numbering_style == s2.paragraph_numbering_style
        }