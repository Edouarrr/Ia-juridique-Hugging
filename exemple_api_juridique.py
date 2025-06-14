"""
Exemple d'utilisation de l'API de génération juridique
Ce fichier montre comment générer des actes sans passer par l'interface Streamlit
"""

import json
from datetime import datetime

from config.cahier_des_charges import get_infraction_details, validate_acte
from modules.generation_juridique import GenerateurActesJuridiques


def exemple_generation_plainte_simple():
    """Exemple : Générer une plainte simple"""
    print("=== GÉNÉRATION D'UNE PLAINTE SIMPLE ===\n")
    
    # Créer le générateur
    generateur = GenerateurActesJuridiques()
    
    # Définir les paramètres
    params = {
        'parties': {
            'demandeurs': ['M. Jean DUPONT'],
            'defendeurs': ['SOCIÉTÉ ALPHA SAS', 'M. Pierre MARTIN (gérant)']
        },
        'infractions': ['Escroquerie', 'Abus de confiance'],
        'contexte': 'Détournement de fonds dans le cadre d\'un contrat de prestation',
        'pieces': [
            {'titre': 'Contrat de prestation du 15/01/2024', 'date': '15/01/2024'},
            {'titre': 'Relevés bancaires', 'date': '01/03/2024'},
            {'titre': 'Échanges de courriels', 'date': '20/02/2024'}
        ]
    }
    
    # Générer l'acte
    acte = generateur.generer_acte('plainte_simple', params)
    
    # Afficher les informations
    print(f"✅ Acte généré : {acte.titre}")
    print(f"📄 Longueur : {acte.metadata['longueur_mots']} mots")
    print(f"📎 Pièces : {len(acte.pieces)} pièces jointes")
    print(f"\n--- EXTRAIT ---")
    print(acte.contenu[:500] + "...")
    
    # Valider selon le CDC
    validation = validate_acte(acte.contenu, 'plainte_simple')
    print(f"\n✅ Validation CDC : {'CONFORME' if validation['valid'] else 'NON CONFORME'}")
    
    # Sauvegarder
    with open(f"plainte_simple_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", 'w', encoding='utf-8') as f:
        f.write(acte.contenu)
    
    return acte

def exemple_generation_plainte_cpc_exhaustive():
    """Exemple : Générer une plainte avec CPC exhaustive (8000+ mots)"""
    print("\n\n=== GÉNÉRATION D'UNE PLAINTE CPC EXHAUSTIVE ===\n")
    
    generateur = GenerateurActesJuridiques()
    generateur.current_phase = 'instruction'  # Phase d'instruction
    
    # Paramètres enrichis pour une plainte complexe
    params = {
        'parties': {
            'demandeurs': [
                {
                    'nom': 'SCI PATRIMOINE INVEST',
                    'forme_juridique': 'Société Civile Immobilière',
                    'siren': '123 456 789',
                    'siege_social': '123 Avenue des Champs, 75008 PARIS',
                    'representant': 'M. Jacques DURAND, gérant'
                }
            ],
            'defendeurs': [
                {
                    'nom': 'GROUPE CONSTRUCTION PLUS SA',
                    'forme_juridique': 'Société Anonyme',
                    'siren': '987 654 321',
                    'siege_social': '456 Boulevard Haussmann, 75009 PARIS',
                    'representant': 'M. André BERNARD, PDG'
                },
                {
                    'nom': 'EXPERTISE COMPTABLE ASSOCIÉS SARL',
                    'forme_juridique': 'SARL',
                    'siren': '456 789 123',
                    'siege_social': '789 Rue de la Paix, 75002 PARIS',
                    'representant': 'Mme Sophie LEFEBVRE, gérante'
                }
            ]
        },
        'infractions': [
            'Abus de biens sociaux',
            'Corruption',
            'Faux et usage de faux',
            'Blanchiment'
        ],
        'contexte': """Vaste opération de détournement de fonds dans le cadre d'un projet immobilier 
        d'envergure. Les faits s'étalent sur une période de 3 ans et impliquent un réseau 
        organisé de sociétés écrans et de montages financiers complexes. Le préjudice total 
        est estimé à plus de 5 millions d'euros.""",
        'pieces': [
            {'titre': 'Rapport d\'audit financier Ernst & Young', 'date': '15/03/2024'},
            {'titre': 'PV d\'assemblée générale extraordinaire', 'date': '20/01/2024'},
            {'titre': 'Contrats de cession d\'actions', 'date': '10/02/2024'},
            {'titre': 'Relevés bancaires société (2021-2024)', 'date': '01/04/2024'},
            {'titre': 'Expertise immobilière contradictoire', 'date': '25/03/2024'},
            {'titre': 'Correspondances entre dirigeants', 'date': '01/01/2024'},
            {'titre': 'Factures et justificatifs comptables', 'date': '31/12/2023'}
        ],
        'options': {
            'style': 'exhaustif',
            'longueur_cible': 8000,
            'inclure_jurisprudence': True,
            'inclure_chronologie': True
        }
    }
    
    # Générer
    print("⏳ Génération en cours (cela peut prendre 1-2 minutes)...")
    acte = generateur.generer_acte('plainte_cpc', params)
    
    # Résultats
    print(f"✅ Acte généré : {acte.titre}")
    print(f"📄 Longueur : {acte.metadata['longueur_mots']} mots")
    print(f"📎 Pièces : {len(acte.pieces)} pièces jointes")
    
    # Validation
    validation = validate_acte(acte.contenu, 'plainte_cpc')
    print(f"\n✅ Validation CDC : {'CONFORME' if validation['valid'] else 'NON CONFORME'}")
    if validation['errors']:
        print("❌ Erreurs :")
        for error in validation['errors']:
            print(f"  - {error}")
    
    # Sauvegarder
    filename = f"plainte_cpc_exhaustive_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(acte.contenu)
    print(f"\n💾 Sauvegardé dans : {filename}")
    
    return acte

def exemple_analyse_requete():
    """Exemple : Analyser des requêtes utilisateur"""
    print("\n\n=== ANALYSE DE REQUÊTES JURIDIQUES ===\n")
    
    from modules.integration_juridique import AnalyseurRequeteJuridique
    
    analyseur = AnalyseurRequeteJuridique()
    
    # Requêtes à tester
    requetes = [
        "rédiger plainte contre Vinci, SOGEPROM et Bouygues pour corruption et abus de biens sociaux @projet_tour_2025",
        "créer conclusions de nullité pour violation article 63 CPP @affaire_martin",
        "générer plainte avec constitution de partie civile exhaustive contre société ABC",
        "recherche simple jurisprudence corruption"  # Pas une génération
    ]
    
    for requete in requetes:
        print(f"\n📝 Requête : \"{requete}\"")
        
        analyse = analyseur.analyser_requete(requete)
        
        print(f"  ➜ Génération détectée : {'✅ OUI' if analyse['is_generation'] else '❌ NON'}")
        if analyse['type_acte']:
            print(f"  ➜ Type d'acte : {analyse['type_acte']}")
        if analyse['parties']['defendeurs']:
            print(f"  ➜ Défendeurs : {', '.join(analyse['parties']['defendeurs'])}")
        if analyse['infractions']:
            print(f"  ➜ Infractions : {', '.join(analyse['infractions'])}")
        if analyse['reference']:
            print(f"  ➜ Référence : @{analyse['reference']}")

def exemple_details_infractions():
    """Exemple : Obtenir les détails des infractions"""
    print("\n\n=== DÉTAILS DES INFRACTIONS ===\n")
    
    infractions = ['abus_biens_sociaux', 'corruption', 'escroquerie']
    
    for code_infraction in infractions:
        details = get_infraction_details(code_infraction)
        if details:
            print(f"\n📖 {details['titre'].upper()}")
            print(f"  • Articles : {', '.join(details['articles'])}")
            print(f"  • Peines : {details['peines']}")
            print(f"  • Prescription : {details['prescription']}")
            print(f"  • Éléments constitutifs :")
            for element in details['elements_constitutifs']:
                print(f"    - {element}")

def exemple_export_json():
    """Exemple : Exporter un acte en JSON pour API"""
    print("\n\n=== EXPORT JSON POUR API ===\n")
    
    # Générer un acte simple
    generateur = GenerateurActesJuridiques()
    params = {
        'parties': {
            'demandeurs': ['API Test Client'],
            'defendeurs': ['API Test Defendant']
        },
        'infractions': ['Escroquerie']
    }
    
    acte = generateur.generer_acte('plainte_simple', params)
    
    # Convertir en JSON
    acte_json = {
        'id': f"acte_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        'type': acte.type_acte,
        'titre': acte.titre,
        'destinataire': acte.destinataire,
        'parties': acte.parties,
        'infractions': acte.infractions,
        'contenu': acte.contenu,
        'metadata': {
            'date_creation': acte.metadata['date_creation'].isoformat(),
            'longueur_mots': acte.metadata['longueur_mots'],
            'phase_procedure': acte.metadata['phase_procedure']
        },
        'pieces': acte.pieces
    }
    
    # Afficher
    print(json.dumps(acte_json, indent=2, ensure_ascii=False)[:500] + "...")
    
    # Sauvegarder
    with open('acte_export.json', 'w', encoding='utf-8') as f:
        json.dump(acte_json, f, indent=2, ensure_ascii=False)
    
    print("\n💾 Exporté dans acte_export.json")

def main():
    """Fonction principale"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║          EXEMPLES D'UTILISATION DE L'API JURIDIQUE          ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Exécuter les exemples
    try:
        # 1. Plainte simple
        exemple_generation_plainte_simple()
        
        # 2. Plainte CPC exhaustive
        # exemple_generation_plainte_cpc_exhaustive()  # Décommenter pour tester
        
        # 3. Analyse de requêtes
        exemple_analyse_requete()
        
        # 4. Détails des infractions
        exemple_details_infractions()
        
        # 5. Export JSON
        exemple_export_json()
        
        print("\n\n✅ Tous les exemples ont été exécutés avec succès !")
        
    except Exception as e:
        print(f"\n\n❌ Erreur : {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()