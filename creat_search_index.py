"""Script pour créer l'index Azure Search pour les documents juridiques"""

import os
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchableField,
    SearchField,
    SearchFieldDataType
)
from azure.core.credentials import AzureKeyCredential

def create_juridique_index():
    """Crée l'index pour les documents juridiques"""
    
    # Configuration
    endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
    key = os.getenv('AZURE_SEARCH_KEY')
    index_name = "juridique-documents"
    
    if not endpoint or not key:
        print("❌ Configuration Azure Search manquante")
        print("Définissez AZURE_SEARCH_ENDPOINT et AZURE_SEARCH_KEY")
        return False
    
    try:
        # Créer le client
        credential = AzureKeyCredential(key)
        index_client = SearchIndexClient(endpoint=endpoint, credential=credential)
        
        # Définir les champs de l'index
        fields = [
            SimpleField(
                name="id",
                type=SearchFieldDataType.String,
                key=True,
                sortable=True,
                filterable=True,
                facetable=True
            ),
            SearchableField(
                name="title",
                type=SearchFieldDataType.String,
                searchable=True,
                filterable=True,
                sortable=True
            ),
            SearchableField(
                name="content",
                type=SearchFieldDataType.String,
                searchable=True,
                analyzer_name="fr.lucene"  # Analyseur français
            ),
            SimpleField(
                name="container",
                type=SearchFieldDataType.String,
                filterable=True,
                facetable=True,
                sortable=True
            ),
            SimpleField(
                name="blob_name",
                type=SearchFieldDataType.String,
                filterable=True,
                sortable=True
            ),
            SimpleField(
                name="document_type",
                type=SearchFieldDataType.String,
                filterable=True,
                facetable=True
            ),
            SimpleField(
                name="last_modified",
                type=SearchFieldDataType.DateTimeOffset,
                filterable=True,
                sortable=True
            ),
            SimpleField(
                name="size",
                type=SearchFieldDataType.Int64,
                filterable=True,
                sortable=True
            ),
            SearchableField(
                name="tags",
                type=SearchFieldDataType.Collection(SearchFieldDataType.String),
                searchable=True,
                filterable=True,
                facetable=True
            ),
            SearchableField(
                name="metadata",
                type=SearchFieldDataType.String,
                searchable=True
            )
        ]
        
        # Créer l'index
        index = SearchIndex(
            name=index_name,
            fields=fields,
            cors_options={
                "allowed_origins": ["*"],
                "max_age_in_seconds": 300
            }
        )
        
        # Vérifier si l'index existe déjà
        try:
            existing_index = index_client.get_index(index_name)
            print(f"⚠️ L'index '{index_name}' existe déjà")
            
            response = input("Voulez-vous le recréer ? (o/n): ")
            if response.lower() == 'o':
                index_client.delete_index(index_name)
                print("🗑️ Index supprimé")
            else:
                print("❌ Opération annulée")
                return False
        except:
            pass
        
        # Créer le nouvel index
        result = index_client.create_index(index)
        print(f"✅ Index '{result.name}' créé avec succès")
        print(f"   - {len(result.fields)} champs définis")
        print(f"   - Analyseur français activé")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la création de l'index: {e}")
        return False

def main():
    print("🔍 Création de l'index Azure Search pour documents juridiques")
    print("-" * 60)
    
    # Vérifier les imports
    try:
        import azure.search.documents
        print("✅ Module azure-search-documents installé")
    except ImportError:
        print("❌ Module azure-search-documents non installé")
        print("Exécutez: pip install azure-search-documents")
        return
    
    # Créer l'index
    if create_juridique_index():
        print("\n✅ Configuration terminée!")
        print("\nProchaines étapes:")
        print("1. Lancer l'application principale")
        print("2. Les documents seront indexés automatiquement")
        print("3. La recherche avancée sera disponible")
    else:
        print("\n❌ Échec de la création de l'index")

if __name__ == "__main__":
    main()