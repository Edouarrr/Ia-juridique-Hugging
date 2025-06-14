import pytest

pytest.importorskip("streamlit")
pytest.importorskip("pandas")
pytest.importorskip("plotly")


from modules.integration_juridique import AnalyseurRequeteJuridiqueAvance


def test_analyseur_basic():
    analyser = AnalyseurRequeteJuridiqueAvance()
    result = analyser.analyser_requete("r\xc3\xa9diger plainte contre X pour fraude")
    assert isinstance(result, dict)
    assert "is_generation" in result


def test_validate_acte():
    from config.cahier_des_charges import validate_acte

    validation = validate_acte("mot " * 100, "plainte_simple")
    assert "valid" in validation
