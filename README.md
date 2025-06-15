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
- **LLMs intégrés** : OpenAI/Azure OpenAI (GPT‑4), Claude, Gemini, Mistral et Groq
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
- `AZURE_SEARCH_ENDPOINT`
- `AZURE_SEARCH_KEY`
- `AZURE_SEARCH_INDEX` *(optionnel, par défaut `juridique-index`)*
- `ANTHROPIC_API_KEY`
- `OPENAI_API_KEY`
- `GOOGLE_API_KEY`
- `MISTRAL_API_KEY`
- `GROQ_API_KEY`

**Note :** Le module `AzureOpenAIManager` fourni est pour l'instant un simple
*placeholder* permettant de charger l'application sans erreur. Vous pouvez
l'utiliser comme base pour une future intégration Azure OpenAI.

## 📚 Guide d'Utilisation

1. **Créer un dossier** : Tab "Dossiers" → Nouveau dossier
2. **Analyser avec l'IA** : Tab "IA Multi-LLM" → Sélectionner LLMs → Poser votre question
3. **Explorer Azure Blob** : Tab "Azure Blob" → Naviguer → Extraire → Analyser
4. **Adapter des plaintes** : Tab "Rédaction" → Charger plainte → Ajouter victimes → Générer
5. **Rechercher** : saisissez une requête dans la barre de recherche. Utilisez `@dossier` pour cibler un dossier précis et choisissez plusieurs IA pour comparer les réponses.
6. **Uploader un dossier local** : depuis l'onglet "Documents", cliquez sur "Importer un dossier" puis sélectionnez votre dossier. Tous les fichiers seront analysés et indexés.

Exemple rapide en code :

```python
from pathlib import Path
from managers.document_manager import DocumentManager

dm = DocumentManager()
files = [open(f, "rb") for f in Path("mon_dossier").iterdir()]
dm.batch_import(files)
```

## 🛡️ Sécurité et Confidentialité

- Les données ne sont pas stockées sur les serveurs
- Les clés API sont sécurisées via Hugging Face Secrets
- Chiffrement des communications
- Respect du secret professionnel

## 🤝 À Propos

Développé pour les avocats spécialisés en droit pénal des affaires, cet assistant combine l'expertise juridique avec les dernières avancées en IA pour optimiser la gestion des dossiers complexes.

## 📄 Licence
Ce projet est distribué sous licence [MIT](LICENSE).

---

Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference