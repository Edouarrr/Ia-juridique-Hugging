"""Script pour analyser quels imports sont réellement utilisés dans votre code"""

import ast
import os
from collections import defaultdict

def extract_imports(file_path):
    """Extrait tous les imports d'un fichier Python"""
    imports = set()
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])
    except Exception as e:
        print(f"Erreur lors de l'analyse de {file_path}: {e}")
    
    return imports

def scan_directory(directory='.'):
    """Scanne tous les fichiers Python du répertoire"""
    all_imports = set()
    file_count = 0
    
    for root, dirs, files in os.walk(directory):
        # Ignorer certains dossiers
        dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'venv', '.env']]
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                imports = extract_imports(file_path)
                all_imports.update(imports)
                file_count += 1
                print(f"Analysé: {file_path} - {len(imports)} imports")
    
    return all_imports, file_count

def map_imports_to_packages():
    """Mapping des imports vers les packages pip"""
    import_to_package = {
        # Standard library (pas besoin d'installer)
        'datetime': 'STDLIB',
        'time': 'STDLIB',
        'json': 'STDLIB',
        'os': 'STDLIB',
        'sys': 'STDLIB',
        'asyncio': 'STDLIB',
        'typing': 'STDLIB',
        'logging': 'STDLIB',
        're': 'STDLIB',
        'hashlib': 'STDLIB',
        'uuid': 'STDLIB',
        
        # Packages externes
        'streamlit': 'streamlit',
        'pandas': 'pandas',
        'numpy': 'numpy',
        'plotly': 'plotly',
        'azure': 'azure-storage-blob / azure-search-documents',
        'openai': 'openai',
        'anthropic': 'anthropic',
        'google': 'google-generativeai',
        'mistralai': 'mistralai',
        'PIL': 'Pillow',
        'docx': 'python-docx',
        'PyPDF2': 'PyPDF2',
        'openpyxl': 'openpyxl',
        'requests': 'requests',
        'bs4': 'beautifulsoup4',
        'dotenv': 'python-dotenv',
        'reportlab': 'reportlab',
        'matplotlib': 'matplotlib',
        'components': 'streamlit',  # Partie de streamlit
    }
    
    return import_to_package

def main():
    print("🔍 Analyse des imports dans votre code...\n")
    
    # Scanner le répertoire
    imports, file_count = scan_directory()
    
    print(f"\n📊 Résumé:")
    print(f"- Fichiers analysés: {file_count}")
    print(f"- Imports uniques trouvés: {len(imports)}")
    
    # Mapper vers les packages
    import_map = map_imports_to_packages()
    
    # Séparer stdlib et packages externes
    stdlib_imports = set()
    external_packages = set()
    unknown_imports = set()
    
    for imp in sorted(imports):
        if imp in import_map:
            if import_map[imp] == 'STDLIB':
                stdlib_imports.add(imp)
            else:
                external_packages.add(import_map[imp])
        else:
            unknown_imports.add(imp)
    
    # Afficher les résultats
    print("\n📦 Packages externes nécessaires:")
    for package in sorted(external_packages):
        print(f"  - {package}")
    
    print(f"\n✅ Modules standard library utilisés ({len(stdlib_imports)}):")
    print(f"  {', '.join(sorted(stdlib_imports))}")
    
    if unknown_imports:
        print(f"\n⚠️ Imports non reconnus ({len(unknown_imports)}):")
        for imp in sorted(unknown_imports):
            print(f"  - {imp}")
    
    # Générer un requirements.txt suggéré
    print("\n📄 requirements.txt suggéré basé sur votre code:")
    print("-" * 50)
    
    requirements = set()
    for package in external_packages:
        if ' / ' in package:
            # Cas spéciaux comme Azure
            for p in package.split(' / '):
                requirements.add(p)
        else:
            requirements.add(package)
    
    for req in sorted(requirements):
        print(req)
    
    print("-" * 50)
    print("\n💡 Note: Ajoutez les versions appropriées (ex: streamlit>=1.28.0)")

if __name__ == "__main__":
    main()