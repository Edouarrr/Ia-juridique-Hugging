# 🤗 Guide de Déploiement sur Hugging Face Spaces

## 🚀 Avantages par rapport à Streamlit Cloud

- ✅ **Python 3.9/3.10** : Compatible avec `azure-ai-openai`
- ✅ **Gratuit** et sans limites de temps
- ✅ **GPU optionnel** pour les modèles lourds
- ✅ **Contrôle total** de l'environnement

## 📋 Étapes de Déploiement

### 1. Créer un compte Hugging Face

1. Allez sur [huggingface.co](https://huggingface.co)
2. Sign Up → Create Account
3. Confirmez votre email

### 2. Créer un nouveau Space

1. Cliquez sur votre profil → **"New Space"**
2. Configurez :
   - **Space name** : `assistant-penal-affaires`
   - **Select SDK** : `Streamlit`
   - **Space hardware** : `CPU basic` (gratuit)
   - **Visibility** : `Private` (recommandé pour données sensibles)
3. Cliquez **"Create Space"**

### 3. Uploader vos fichiers

#### Option A : Interface Web (Simple)
1. Dans votre Space, cliquez **"Files"**
2. **Drag & drop** ces fichiers :
   - `app.py` (votre application principale)
   - `requirements.txt` (celui pour HuggingFace)
   - `README.md`
   - `.gitignore`
   - Tous vos autres fichiers Python

#### Option B : Git (Avancé)
```bash
# Cloner votre Space
git clone https://huggingface.co/spaces/VOTRE_USERNAME/assistant-penal-affaires

# Copier vos fichiers
cp app.py requirements.txt README.md .gitignore assistant-penal-affaires/

# Commit et push
cd assistant-penal-affaires
git add .
git commit -m "Initial deployment"
git push
```

### 4. Configurer les Secrets

1. Dans votre Space → **"Settings"**
2. Scroll jusqu'à **"Variables and secrets"**
3. Cliquez **"New secret"** pour chaque clé :

```
AZURE_OPENAI_ENDPOINT → https://votre-resource.openai.azure.com/
AZURE_OPENAI_KEY → votre-clé-azure
AZURE_OPENAI_DEPLOYMENT → gpt-4

AZURE_STORAGE_CONNECTION_STRING → DefaultEndpointsProtocol=https;...

ANTHROPIC_API_KEY → sk-ant-api03-...
OPENAI_API_KEY → sk-...
GOOGLE_API_KEY → AIzaSy...
PERPLEXITY_API_KEY → pplx-...
```

### 5. Vérifier le déploiement

1. Le Space va **builder automatiquement** (2-5 minutes)
2. Regardez les **logs** en cas d'erreur
3. Une fois vert → Votre app est live !

## 📁 Structure des Fichiers

```
assistant-penal-affaires/
├── app.py                  # ✅ Votre code ORIGINAL (pas de modifications!)
├── requirements.txt        # ✅ Version avec azure-ai-openai
├── README.md              # ✅ Description du Space
├── .gitignore             # ✅ Fichiers à ignorer
└── [vos autres fichiers]   # Tous vos modules Python
```

## 🔧 Différences avec votre Code Original

**AUCUNE !** 🎉

Sur Hugging Face, vous pouvez utiliser :
- ✅ `azure-ai-openai==1.10.0`
- ✅ Votre code original sans modifications
- ✅ Toutes vos fonctionnalités

## 🧪 Test Rapide

1. **D'abord**, uploadez `app_check_huggingface.py`
2. Renommez temporairement :
   - `app.py` → `app_original.py`
   - `app_check_huggingface.py` → `app.py`
3. Laissez builder et testez
4. Si tout est ✅, revenez à votre app originale

## 🛠️ Dépannage

### Erreur de build
- Vérifiez `requirements.txt`
- Regardez les logs complets
- Essayez avec moins de dépendances

### Modules non trouvés
- Assurez-vous que TOUS vos fichiers .py sont uploadés
- Vérifiez la structure des imports

### Secrets non reconnus
- Les noms doivent être EXACTEMENT identiques
- Pas d'espaces dans les noms
- Redémarrez le Space après ajout

## 🎯 Checklist Finale

- [ ] Compte Hugging Face créé
- [ ] Space créé en mode Streamlit
- [ ] Fichiers uploadés :
  - [ ] app.py (original)
  - [ ] requirements.txt (avec azure-ai-openai)
  - [ ] README.md
  - [ ] .gitignore
  - [ ] Tous vos modules
- [ ] Secrets configurés (8 au total)
- [ ] Build réussi (logs verts)
- [ ] Application accessible

## 🚀 URL de votre Application

Une fois déployée :
```
https://huggingface.co/spaces/VOTRE_USERNAME/assistant-penal-affaires
```

Ou si embed :
```
https://VOTRE_USERNAME-assistant-penal-affaires.hf.space
```

## 💡 Astuces Pro

1. **Logs en temps réel** : Settings → Logs
2. **Restart rapide** : Settings → Restart Space
3. **Backup** : Dupliquez le Space avant modifications majeures
4. **Performance** : Passez à GPU si besoin (payant)

---

**C'est tout !** Votre application fonctionnera parfaitement sur Hugging Face avec toutes les fonctionnalités Azure ! 🎉