# ✅ Checklist d'intégration du module juridique

## 📁 Fichiers à créer

### Configuration
- [ ] `config/cahier_des_charges.py` - Configuration complète du CDC
- [ ] `config/__init__.py` - Assurez-vous qu'il existe

### Modules principaux
- [ ] `modules/generation_juridique.py` - Générateur d'actes
- [ ] `modules/integration_juridique.py` - Intégration avec la recherche
- [ ] `modules/export_juridique.py` - Export Word/PDF
- [ ] `modules/__init__.py` - Assurez-vous qu'il existe

### Services
- [ ] `services/pappers_service.py` - Enrichissement sociétés
- [ ] `services/__init__.py` - Créez-le s'il n'existe pas

### Utilitaires
- [ ] `utils/cache_juridique.py` - Système de cache
- [ ] `utils/__init__.py` - Assurez-vous qu'il existe

### Tests et documentation
- [ ] `test_integration_juridique.py` - Tests de vérification
- [ ] `exemple_api_juridique.py` - Exemples d'utilisation
- [ ] `GUIDE_INTEGRATION_JURIDIQUE.md` - Documentation

## 🔧 Modifications de fichiers existants

### modules/recherche.py
- [ ] Ajouter les imports du module juridique
- [ ] Modifier `__init__` de `SearchInterface` pour ajouter l'analyseur
- [ ] Modifier `process_universal_query` pour détecter les requêtes juridiques
- [ ] Ajouter `_process_juridique_request`
- [ ] Ajouter le bouton "⚖️ Actes juridiques" dans `show_quick_actions`
- [ ] Mettre à jour les exemples de commandes
- [ ] Ajouter `show_juridique_results` dans `show_unified_results`

### requirements.txt
- [ ] Ajouter `python-docx>=0.8.11`
- [ ] Ajouter `reportlab>=3.6.0`
- [ ] Ajouter `pypdf>=3.0.0`
- [ ] Ajouter `requests>=2.28.0`
- [ ] Vérifier les versions des autres dépendances

### app.py (si nécessaire)
- [ ] Importer les nouveaux modules
- [ ] Ajouter l'initialisation du cache (optionnel)

## 🔑 Configuration

### Variables d'environnement
- [ ] `ANTHROPIC_API_KEY` ou `OPENAI_API_KEY` (au moins une)
- [ ] `PAPPERS_API_KEY` (optionnel mais recommandé)
- [ ] Variables Azure si utilisées

### Personnalisation
- [ ] Modifier `CABINET_INFO` dans `cahier_des_charges.py`
- [ ] Adapter les infractions si nécessaire
- [ ] Personnaliser les templates si besoin

## 🧪 Tests de vérification

### Test 1 : Imports
```bash
streamlit run test_integration_juridique.py
```
- [ ] Tous les imports passent
- [ ] L'analyseur fonctionne
- [ ] La génération simple fonctionne
- [ ] La validation CDC fonctionne

### Test 2 : Recherche universelle
Dans l'application principale :
- [ ] Taper : `rédiger plainte contre X pour escroquerie`
- [ ] L'interface de génération s'affiche
- [ ] Les parties et infractions sont détectées

### Test 3 : Génération complète
- [ ] Générer une plainte simple
- [ ] Générer une plainte CPC (longue)
- [ ] Vérifier la mise en forme
- [ ] Tester l'export Word/PDF

### Test 4 : Enrichissement (si Pappers configuré)
- [ ] Rechercher une société connue (ex: Vinci)
- [ ] Les informations sont enrichies automatiquement
- [ ] Le SIREN et l'adresse apparaissent

### Test 5 : Cache
- [ ] Générer un acte
- [ ] Le regénérer avec les mêmes paramètres
- [ ] Vérifier qu'il est chargé depuis le cache

## 🚀 Déploiement

### Local
- [ ] `pip install -r requirements.txt`
- [ ] `streamlit run app.py`
- [ ] Tout fonctionne localement

### Hugging Face
- [ ] Commit tous les fichiers
- [ ] Push vers Hugging Face
- [ ] Build réussi sans erreurs
- [ ] Application accessible en ligne
- [ ] Tests de génération réussis

## 📊 Vérifications finales

### Fonctionnalités
- [ ] ✅ 8 types d'actes disponibles
- [ ] ✅ Détection automatique des requêtes
- [ ] ✅ Extraction parties/infractions
- [ ] ✅ Mise en forme Garamond
- [ ] ✅ Hiérarchie I > A > 1 > a > i)
- [ ] ✅ Export Word/PDF fonctionnel
- [ ] ✅ Enrichissement sociétés (si configuré)
- [ ] ✅ Cache opérationnel
- [ ] ✅ Validation CDC

### Performance
- [ ] Génération < 2 minutes
- [ ] Export < 10 secondes
- [ ] Cache fonctionne
- [ ] Pas d'erreur mémoire

### Qualité
- [ ] Actes conformes au CDC
- [ ] Longueur respectée
- [ ] Structure correcte
- [ ] Pas de placeholder [À COMPLÉTER]

## 🎯 Quick Start

Une fois tout vérifié, testez ces commandes :

```
1. rédiger plainte contre Vinci pour abus de biens sociaux
2. créer conclusions de nullité @affaire_test
3. générer plainte CPC exhaustive contre SOGEPROM, Alpha SAS
4. écrire observations article 175 CPP
5. Cliquer sur "⚖️ Actes juridiques"
```

## 📈 Métriques de succès

- [ ] Temps de génération divisé par 10 minimum
- [ ] 0 erreur de conformité CDC
- [ ] Export professionnel fonctionnel
- [ ] Utilisateurs satisfaits de la qualité

## 🆘 En cas de problème

1. Vérifiez les logs Streamlit
2. Consultez `test_integration_juridique.py`
3. Vérifiez les imports dans la console
4. Assurez-vous que les API keys sont définies
5. Vérifiez l'espace disque disponible

---

**✅ Une fois toute la checklist complétée, votre module juridique est opérationnel !**

*Dernière mise à jour : [DATE]*
*Version : 1.0.0*