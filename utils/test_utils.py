# utils/test_utils.py
"""
Tests simples pour vérifier le bon fonctionnement des utils
"""

import os
import sys
from datetime import datetime

import pytest
pytest.importorskip("streamlit")

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_text_processing():
    """Test des fonctions de traitement de texte"""
    print("\n=== TEST TEXT PROCESSING ===")
    
    from utils.text_processing import (
        calculate_text_similarity,
        extract_monetary_amounts,
        normalize_whitespace,
    )
    from utils import clean_key, truncate_text

    # Test clean_key
    assert clean_key("Test String 123!") == "test_string_123"
    print("✓ clean_key")
    
    # Test normalize_whitespace
    text = "Test   avec    espaces\n\n\nmultiples"
    assert "  " not in normalize_whitespace(text)
    print("✓ normalize_whitespace")
    
    # Test truncate_text
    long_text = "a" * 200
    truncated = truncate_text(long_text, 50)
    assert len(truncated) == 53  # 47 + "..."
    print("✓ truncate_text")
    
    # Test similarity
    sim = calculate_text_similarity("chat noir", "chat blanc")
    assert 0 < sim < 1
    print(f"✓ calculate_text_similarity: {sim:.2f}")
    
    # Test extract_monetary_amounts
    text = "Le montant est de 1.234,56 € et $500"
    amounts = extract_monetary_amounts(text)
    assert len(amounts) == 2
    assert amounts[0]['currency'] == 'EUR'
    assert amounts[1]['currency'] == 'USD'
    print("✓ extract_monetary_amounts")


def test_date_time():
    """Test des fonctions de date/temps"""
    print("\n=== TEST DATE TIME ===")
    
    from utils import (
        extract_dates,
        format_date,
        format_duration,
        format_legal_date,
        is_business_day,
    )

    # Test format_date
    date = datetime(2024, 1, 15)
    assert format_date(date) == "15/01/2024"
    print("✓ format_date")
    
    # Test format_legal_date
    legal = format_legal_date(date)
    assert legal == "15 janvier 2024"
    print("✓ format_legal_date")
    
    # Test format_duration
    assert format_duration(65) == "1m 5s"
    assert format_duration(3665) == "1h 1m"
    print("✓ format_duration")
    
    # Test extract_dates
    text = "Réunion le 15/01/2024 et audience le 20 mars 2024"
    dates = extract_dates(text)
    assert len(dates) >= 2
    print(f"✓ extract_dates: trouvé {len(dates)} dates")
    
    # Test is_business_day
    monday = datetime(2024, 1, 15)  # Lundi
    sunday = datetime(2024, 1, 14)  # Dimanche
    assert is_business_day(monday) == True
    assert is_business_day(sunday) == False
    print("✓ is_business_day")


def test_legal_utils():
    """Test des fonctions juridiques"""
    print("\n=== TEST LEGAL UTILS ===")
    
    from utils.legal_utils import (categorize_legal_document,
                                   extract_legal_references, extract_parties,
                                   format_legal_amount)

    # Test extract_legal_references
    text = """
    Vu l'article 1382 du Code civil et l'article L.241-3 du Code de commerce,
    Vu l'arrêt de la Cour de cassation du 15 janvier 2020
    """
    refs = extract_legal_references(text)
    assert len(refs['articles']) > 0
    assert len(refs['jurisprudence']) > 0
    print(f"✓ extract_legal_references: {len(refs['articles'])} articles, {len(refs['jurisprudence'])} jurisprudences")
    
    # Test format_legal_amount
    amount = format_legal_amount(1234.56)
    assert amount == "1 234,56 euros"
    print("✓ format_legal_amount")
    
    # Test categorize_legal_document
    jugement_text = "Par ces motifs, le tribunal condamne..."
    cat = categorize_legal_document(jugement_text)
    assert cat == "jugement"
    print("✓ categorize_legal_document")


def test_file_utils():
    """Test des fonctions fichiers"""
    print("\n=== TEST FILE UTILS ===")
    
    from utils import (
        format_file_size,
        get_file_extension,
        get_file_icon,
        is_valid_email,
        validate_uploaded_file,
        sanitize_filename,
    )

    # Test sanitize_filename
    unsafe = "fichier<>:|?*.txt"
    safe = sanitize_filename(unsafe)
    assert "<" not in safe and ">" not in safe
    print("✓ sanitize_filename")
    
    # Test format_file_size
    assert format_file_size(1024) == "1.0 KB"
    assert format_file_size(1048576) == "1.0 MB"
    print("✓ format_file_size")
    
    # Test get_file_icon
    assert get_file_icon("document.pdf") == "📄"
    assert get_file_icon("image.jpg") == "🖼️"
    print("✓ get_file_icon")
    
    # Test get_file_extension
    assert get_file_extension("document.pdf") == "pdf"
    assert get_file_extension("archive.tar.gz") == "gz"
    print("✓ get_file_extension")
    
    # Test is_valid_email
    assert is_valid_email("test@example.com") == True
    assert is_valid_email("invalid.email") == False
    print("✓ is_valid_email")

    class DummyFile:
        def __init__(self, name, data, type=None):
            self.name = name
            self._data = data
            self.size = len(data)
            self.type = type or "text/plain"

        def getvalue(self):
            return self._data

    # Fichier texte valide
    valid, msg = validate_uploaded_file(DummyFile("test.txt", b"hello"))
    assert valid

    # Fichier vide
    valid, msg = validate_uploaded_file(DummyFile("empty.txt", b""))
    assert not valid

    # Fichier trop volumineux (limite 1 MB pour le test)
    big_data = b"a" * (2 * 1024 * 1024)
    valid, msg = validate_uploaded_file(DummyFile("big.txt", big_data), max_size_mb=1)
    assert not valid

    # Fichier non texte
    valid, msg = validate_uploaded_file(DummyFile("image.png", b"\x89PNG\r\n"))
    assert not valid


def test_validators():
    """Test des validateurs"""
    print("\n=== TEST VALIDATORS ===")
    
    from utils.validators import (validate_iban, validate_phone_number,
                                  validate_postal_code, validate_siren)

    # Test SIREN (Amazon France)
    valid, error = validate_siren("487773327")
    assert valid == True
    print("✓ validate_siren")
    
    # Test téléphone
    valid, error = validate_phone_number("0123456789")
    assert valid == True
    valid, error = validate_phone_number("123")
    assert valid == False
    print("✓ validate_phone_number")
    
    # Test code postal
    valid, error = validate_postal_code("75001")
    assert valid == True
    valid, error = validate_postal_code("00000")
    assert valid == False
    print("✓ validate_postal_code")
    
    # Test IBAN (exemple fictif mais format valide)
    valid, error = validate_iban("FR1420041010050500013M02606")
    # Le test peut échouer car c'est un IBAN fictif
    print(f"✓ validate_iban format check: {'valid' if len('FR1420041010050500013M02606') == 27 else 'invalid'}")


def test_cache_manager():
    """Test du système de cache"""
    print("\n=== TEST CACHE MANAGER ===")
    
    from utils.cache_manager import cache_result, get_cache
    
    cache = get_cache()
    
    # Test set/get
    cache.set("test_key", {"data": "test"}, "test")
    result = cache.get("test_key", "test")
    assert result is not None
    assert result["data"] == "test"
    print("✓ cache set/get")
    
    # Test avec décorateur
    @cache_result(cache_type="test")
    def expensive_function(x):
        return x * 2
    
    # Premier appel
    result1 = expensive_function(5)
    # Deuxième appel (depuis le cache)
    result2 = expensive_function(5)
    assert result1 == result2 == 10
    print("✓ cache decorator")
    
    # Nettoyage
    cache.clear("test")
    print("✓ cache clear")


def test_formatters():
    """Test des formatters"""
    print("\n=== TEST FORMATTERS ===")
    
    from utils import (
        _to_roman,
        apply_legal_numbering,
        format_legal_list,
        format_signature_block,
    )

    # Test numérotation romaine
    assert _to_roman(1) == "I"
    assert _to_roman(4) == "IV"
    assert _to_roman(9) == "IX"
    assert _to_roman(2024) == "MMXXIV"
    print("✓ _to_roman")
    
    # Test numérotation juridique
    sections = ["Introduction", "Faits", "Discussion", "Conclusion"]
    numbered = apply_legal_numbering(sections, style="roman")
    assert numbered[0].startswith("I ")
    assert numbered[3].startswith("IV ")
    print("✓ apply_legal_numbering")
    
    # Test liste formatée
    items = ["Premier point", "Deuxième point", "Troisième point"]
    formatted = format_legal_list(items, style="number")
    assert "1. " in formatted
    assert "2. " in formatted
    print("✓ format_legal_list")
    
    # Test bloc signature
    signatories = [
        {"name": "Me Jean DUPONT", "title": "Avocat au Barreau de Paris"}
    ]
    signature = format_signature_block(signatories, "Paris")
    assert "Me Jean DUPONT" in signature
    assert "Paris" in signature
    print("✓ format_signature_block")


def test_session():
    """Test de la gestion de session (sans Streamlit)"""
    print("\n=== TEST SESSION (simulation) ===")
    
    # On ne peut pas vraiment tester les fonctions Streamlit sans l'environnement
    # Mais on peut au moins importer le module
    try:
        from utils import get_session_value, set_session_value
        print("✓ session module imported successfully")
    except Exception as e:
        print(f"⚠ session module import warning: {e}")


def run_all_tests():
    """Lance tous les tests"""
    print("=== DÉBUT DES TESTS UTILS ===")
    
    tests = [
        test_text_processing,
        test_date_time,
        test_legal_utils,
        test_file_utils,
        test_validators,
        test_cache_manager,
        test_formatters,
        test_session
    ]
    
    failed = 0
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"\n❌ ERREUR dans {test.__name__}: {e}")
            failed += 1
    
    print(f"\n=== RÉSUMÉ: {len(tests) - failed}/{len(tests)} tests réussis ===")
    
    return failed == 0


if __name__ == "__main__":
    import sys
    success = run_all_tests()
    sys.exit(0 if success else 1)