---
title: Assistant Pénal des Affaires IA
emoji: 💼
colorFrom: indigo
colorTo: blue
sdk: streamlit
sdk_version: 1.45.1
app_file: app.py
pinned: false
---

# 💼 Assistant Pénal des Affaires IA

Application spécialisée dans l'assistance juridique en droit pénal des affaires français, intégrant plusieurs LLMs et Azure Blob Storage.

## 🌟 Fonctionnalités Principales

### 📂 Gestion de Dossiers
- Création et suivi de dossiers pénaux complexes
- Gestion multi-victimes avec adaptation automatique
- Calcul automatique des délais de prescription
- Analyse de risques spécialisée (ABS, corruption, etc.)

### 🤖 IA Multi-LLM
- **5 LLMs intégrés** : Azure OpenAI, Claude Opus 4, ChatGPT 4o, Gemini, Perplexity
- Interrogation simple ou multiple avec comparaison
- Fusion intelligente des réponses pour une analyse complète
- Templates de prompts juridiques pré-configurés

### ☁️ Azure Blob Storage
- Navigation intuitive dans les dossiers
- Extraction automatique de documents (PDF, DOCX, TXT)
- Analyse groupée par IA de dossiers complets
- Export en masse avec conservation de l'arborescence

### ✍️ Rédaction Assistée
- Modèles d'actes juridiques (plaintes, conclusions, CJIP)
- Adaptation automatique multi-victimes
- Export Word avec en-tête personnalisé
- Versement automatique aux débats

## 🔐 Configuration

Pour utiliser toutes les fonctionnalités, configurez vos clés API dans les Settings du Space :

- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_KEY`
- `AZURE_OPENAI_DEPLOYMENT`
- `AZURE_STORAGE_CONNECTION_STRING`
- `ANTHROPIC_API_KEY`
- `OPENAI_API_KEY`
- `GOOGLE_API_KEY`
- `PERPLEXITY_API_KEY`

## 📚 Guide d'Utilisation

1. **Créer un dossier** : Tab "Dossiers" → Nouveau dossier
2. **Analyser avec l'IA** : Tab "IA Multi-LLM" → Sélectionner LLMs → Poser votre question
3. **Explorer Azure Blob** : Tab "Azure Blob" → Naviguer → Extraire → Analyser
4. **Adapter des plaintes** : Tab "Rédaction" → Charger plainte → Ajouter victimes → Générer

## 🛡️ Sécurité et Confidentialité

- Les données ne sont pas stockées sur les serveurs
- Les clés API sont sécurisées via Hugging Face Secrets
- Chiffrement des communications
- Respect du secret professionnel

## 🤝 À Propos

Développé pour les avocats spécialisés en droit pénal des affaires, cet assistant combine l'expertise juridique avec les dernières avancées en IA pour optimiser la gestion des dossiers complexes.

---

Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference