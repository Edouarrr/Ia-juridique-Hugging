# managers/llm_manager.py
"""
Gestionnaire LLM principal pour l'application juridique
"""

import logging
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

# Import du gestionnaire multi-LLM
try:
    from managers.multi_llm_manager import MultiLLMManager
    MULTI_LLM_AVAILABLE = True
except ImportError:
    MULTI_LLM_AVAILABLE = False
    
# Import conditionnel de Groq (fallback)
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

# Import conditionnel d'OpenAI
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMManager:
    """
    Gestionnaire LLM unifié qui peut utiliser MultiLLMManager ou des providers directs
    """
    
    def __init__(self):
        self.multi_llm = None
        self.default_provider = None
        self.groq_client = None
        self.openai_client = None
        self._initialize()
        
    def _initialize(self):
        """Initialise le gestionnaire LLM avec les providers disponibles"""
        
        # Essayer d'abord MultiLLMManager s'il est disponible
        if MULTI_LLM_AVAILABLE:
            try:
                self.multi_llm = MultiLLMManager()
                available_providers = self.multi_llm.get_available_providers()
                if available_providers:
                    self.default_provider = available_providers[0]
                    logger.info(f"MultiLLMManager initialisé avec {len(available_providers)} providers")
                    return
            except Exception as e:
                logger.warning(f"Impossible d'initialiser MultiLLMManager: {e}")
        
        # Fallback sur Groq direct
        if GROQ_AVAILABLE and os.getenv("GROQ_API_KEY"):
            try:
                self.groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
                self.default_provider = "groq"
                logger.info("Groq initialisé en mode direct")
            except Exception as e:
                logger.error(f"Erreur initialisation Groq: {e}")
        
        # Fallback sur OpenAI direct
        if not self.default_provider and OPENAI_AVAILABLE and os.getenv("OPENAI_API_KEY"):
            try:
                self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                self.default_provider = "openai"
                logger.info("OpenAI initialisé en mode direct")
            except Exception as e:
                logger.error(f"Erreur initialisation OpenAI: {e}")
        
        if not self.default_provider:
            logger.error("Aucun provider LLM disponible!")
            raise ValueError("Aucun provider LLM configuré. Vérifiez vos clés API.")
    
    def generate(
        self,
        prompt: str,
        system_prompt: str = "Tu es un assistant juridique expert en droit français.",
        temperature: float = 0.7,
        max_tokens: int = 4000,
        provider: Optional[str] = None
    ) -> str:
        """
        Génère une réponse en utilisant le LLM
        
        Args:
            prompt: Le prompt utilisateur
            system_prompt: Le prompt système
            temperature: Température de génération
            max_tokens: Nombre max de tokens
            provider: Provider spécifique à utiliser
            
        Returns:
            La réponse générée
        """
        prompt = MultiLLMManager._prepend_prioritized_pieces(prompt)

        try:
            # Utiliser MultiLLMManager si disponible
            if self.multi_llm and (provider in self.multi_llm.get_available_providers() or not provider):
                result = self.multi_llm.query_single_llm(
                    provider or self.default_provider,
                    prompt,
                    system_prompt,
                    temperature,
                    max_tokens
                )
                
                if result['success']:
                    return result['response']
                else:
                    logger.error(f"Erreur MultiLLM: {result.get('error')}")
                    # Continuer avec fallback
            
            # Fallback sur Groq direct
            if self.groq_client and (provider == "groq" or not provider):
                return self._generate_groq(prompt, system_prompt, temperature, max_tokens)
            
            # Fallback sur OpenAI direct
            if self.openai_client and (provider == "openai" or not provider):
                return self._generate_openai(prompt, system_prompt, temperature, max_tokens)
            
            # Si aucun provider n'est disponible
            raise RuntimeError("Aucun provider LLM disponible pour générer la réponse")
            
        except Exception as e:
            logger.error(f"Erreur génération LLM: {e}")
            raise
    
    def _generate_groq(self, prompt: str, system_prompt: str, temperature: float, max_tokens: int) -> str:
        """Génère avec Groq en direct"""
        try:
            response = self.groq_client.chat.completions.create(
                model="mixtral-8x7b-32768",  # ou "llama3-70b-8192"
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Erreur Groq: {e}")
            raise
    
    def _generate_openai(self, prompt: str, system_prompt: str, temperature: float, max_tokens: int) -> str:
        """Génère avec OpenAI en direct"""
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",  # ou "gpt-3.5-turbo"
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Erreur OpenAI: {e}")
            raise
    
    def analyze_legal_document(
        self,
        document_text: str,
        analysis_type: str = "complete"
    ) -> Dict[str, Any]:
        """
        Analyse un document juridique
        
        Args:
            document_text: Le texte du document
            analysis_type: Type d'analyse (complete, summary, risks)
            
        Returns:
            Dictionnaire avec les résultats d'analyse
        """
        
        prompts = {
            "complete": """
                Analysez ce document juridique de manière complète:
                1. Type et nature du document
                2. Parties impliquées
                3. Points juridiques clés
                4. Risques identifiés
                5. Opportunités
                6. Recommandations
                
                Document:
                {document}
            """,
            "summary": """
                Résumez ce document juridique en identifiant:
                1. L'objet principal
                2. Les parties
                3. Les points essentiels
                
                Document:
                {document}
            """,
            "risks": """
                Analysez les risques juridiques dans ce document:
                1. Risques contractuels
                2. Risques de contentieux
                3. Points de vigilance
                4. Recommandations pour mitiger les risques
                
                Document:
                {document}
            """
        }
        
        prompt = prompts.get(analysis_type, prompts["complete"]).format(
            document=document_text[:8000]  # Limiter la taille
        )
        
        try:
            analysis = self.generate(
                prompt=prompt,
                system_prompt="Tu es un expert juridique spécialisé dans l'analyse de documents légaux français.",
                temperature=0.3,  # Température basse pour plus de précision
                max_tokens=2000
            )
            
            return {
                "success": True,
                "analysis": analysis,
                "type": analysis_type,
                "timestamp": datetime.now().isoformat(),
                "document_length": len(document_text),
                "provider": self.default_provider
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "type": analysis_type,
                "timestamp": datetime.now().isoformat()
            }
    
    def generate_legal_document(
        self,
        document_type: str,
        context: Dict[str, Any],
        template: Optional[str] = None
    ) -> str:
        """
        Génère un document juridique
        
        Args:
            document_type: Type de document (plainte, conclusions, etc.)
            context: Contexte et informations pour le document
            template: Template optionnel à suivre
            
        Returns:
            Le document généré
        """
        
        # Construire le prompt selon le type de document
        base_prompts = {
            "plainte": """
                Rédigez une plainte pénale formelle avec les éléments suivants:
                - Plaignant: {plaignant}
                - Défendeur: {defendeur}
                - Faits: {faits}
                - Fondements juridiques: {fondements}
                
                La plainte doit être structurée avec:
                1. En-tête et destinataire
                2. Identification des parties
                3. Exposé chronologique des faits
                4. Qualification juridique
                5. Demandes
                6. Pièces justificatives
            """,
            "conclusions": """
                Rédigez des conclusions d'avocat avec:
                - Client: {client}
                - Adversaire: {adversaire}
                - Procédure: {procedure}
                - Arguments: {arguments}
                
                Structure:
                1. Rappel de la procédure
                2. Faits et procédure
                3. Discussion juridique
                4. Dispositif
            """,
            "assignation": """
                Rédigez une assignation en justice:
                - Demandeur: {demandeur}
                - Défendeur: {defendeur}
                - Tribunal: {tribunal}
                - Objet: {objet}
                
                Respectez le formalisme du Code de procédure civile.
            """
        }
        
        # Utiliser le template personnalisé ou le template par défaut
        if template:
            prompt = template.format(**context)
        else:
            prompt_template = base_prompts.get(document_type, """
                Rédigez un document juridique de type {document_type} avec les informations suivantes:
                {context}
            """)
            
            if document_type in base_prompts:
                prompt = prompt_template.format(**context)
            else:
                prompt = prompt_template.format(
                    document_type=document_type,
                    context=str(context)
                )
        
        # Générer le document
        system_prompt = f"""
        Tu es un avocat expert en droit français. Tu rédiges des documents juridiques 
        professionnels, précis et conformes aux exigences légales françaises.
        Tu utilises le vocabulaire juridique approprié et respectes les formalismes requis.
        """
        
        try:
            document = self.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.3,  # Basse température pour la précision
                max_tokens=4000
            )
            
            return document
            
        except Exception as e:
            logger.error(f"Erreur génération document: {e}")
            raise
    
    def compare_documents(
        self,
        doc1: str,
        doc2: str,
        comparison_type: str = "differences"
    ) -> Dict[str, Any]:
        """
        Compare deux documents juridiques
        
        Args:
            doc1: Premier document
            doc2: Second document
            comparison_type: Type de comparaison (differences, similarities, full)
            
        Returns:
            Résultats de la comparaison
        """
        
        prompts = {
            "differences": """
                Comparez ces deux documents juridiques et identifiez:
                1. Les différences principales
                2. Les clauses contradictoires
                3. Les éléments présents dans l'un mais pas l'autre
                
                Document 1:
                {doc1}
                
                Document 2:
                {doc2}
            """,
            "similarities": """
                Identifiez les points communs entre ces documents:
                1. Clauses similaires
                2. Principes juridiques partagés
                3. Structure commune
                
                Document 1:
                {doc1}
                
                Document 2:
                {doc2}
            """,
            "full": """
                Effectuez une comparaison complète de ces documents:
                1. Points communs
                2. Différences
                3. Analyse des implications juridiques
                4. Recommandations
                
                Document 1:
                {doc1}
                
                Document 2:
                {doc2}
            """
        }
        
        prompt = prompts.get(comparison_type, prompts["full"]).format(
            doc1=doc1[:4000],
            doc2=doc2[:4000]
        )
        
        try:
            comparison = self.generate(
                prompt=prompt,
                system_prompt="Tu es un expert en analyse comparative de documents juridiques.",
                temperature=0.3,
                max_tokens=2000
            )
            
            return {
                "success": True,
                "comparison": comparison,
                "type": comparison_type,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "type": comparison_type,
                "timestamp": datetime.now().isoformat()
            }
    
    def extract_key_information(self, document: str) -> Dict[str, Any]:
        """
        Extrait les informations clés d'un document juridique
        
        Args:
            document: Le document à analyser
            
        Returns:
            Dictionnaire avec les informations extraites
        """
        
        prompt = """
        Extrayez les informations suivantes du document juridique:
        
        1. Type de document
        2. Parties impliquées (noms et qualités)
        3. Date(s) importante(s)
        4. Montants mentionnés
        5. Juridiction compétente
        6. Numéros de référence (RG, etc.)
        7. Délais mentionnés
        8. Obligations principales
        
        Présentez les informations de manière structurée.
        
        Document:
        {document}
        """.format(document=document[:5000])
        
        try:
            extraction = self.generate(
                prompt=prompt,
                system_prompt="Tu es un expert en extraction d'informations juridiques. Sois précis et exhaustif.",
                temperature=0.1,  # Très basse pour la précision
                max_tokens=1500
            )
            
            return {
                "success": True,
                "extraction": extraction,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_available_providers(self) -> List[str]:
        """Retourne la liste des providers disponibles"""
        if self.multi_llm:
            return self.multi_llm.get_available_providers()
        
        providers = []
        if self.groq_client:
            providers.append("groq")
        if self.openai_client:
            providers.append("openai")
        
        return providers
    
    def test_connection(self) -> Dict[str, bool]:
        """Teste la connexion aux LLMs"""
        results = {}
        
        if self.multi_llm:
            return self.multi_llm.test_connections()
        
        # Test direct
        test_prompt = "Réponds simplement 'OK'"
        
        if self.groq_client:
            try:
                response = self._generate_groq(test_prompt, "Réponds uniquement 'OK'", 0.1, 10)
                results["groq"] = "OK" in response
            except:
                results["groq"] = False
        
        if self.openai_client:
            try:
                response = self._generate_openai(test_prompt, "Réponds uniquement 'OK'", 0.1, 10)
                results["openai"] = "OK" in response
            except:
                results["openai"] = False
        
        return results
    
    def debug_info(self) -> Dict[str, Any]:
        """Retourne des informations de debug"""
        info = {
            "multi_llm_available": MULTI_LLM_AVAILABLE,
            "groq_available": GROQ_AVAILABLE,
            "openai_available": OPENAI_AVAILABLE,
            "default_provider": self.default_provider,
            "available_providers": self.get_available_providers(),
            "has_groq_key": bool(os.getenv("GROQ_API_KEY")),
            "has_openai_key": bool(os.getenv("OPENAI_API_KEY"))
        }
        
        return info

# Fonction utilitaire pour créer une instance
_llm_manager_instance = None

def get_llm_manager() -> LLMManager:
    """Retourne une instance singleton du LLMManager"""
    global _llm_manager_instance
    if _llm_manager_instance is None:
        _llm_manager_instance = LLMManager()
    return _llm_manager_instance