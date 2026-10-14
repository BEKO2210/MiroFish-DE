"""Kaltabruf-Prompt darf keine versteckten starken Begriffe enthalten."""
import pytest

from scripts import validate_case as vc


def test_cold_prompt_with_hidden_strong_term_aborts_before_sending():
    sent = []
    with pytest.raises(ValueError, match="Kaltabruf abgebrochen"):
        vc.check_contamination(
            "Musterstadt 2021", llm=lambda model, prompt: sent.append(prompt) or "",
            material="Ausgangslage ohne Details.", topic="Beschluss GEBÜHR 4711",
            hidden_outcomes=[{"text_de": "Frage?", "quelle": "Bericht vom 12.03.2022"}],
            verlauf="Der Rat beschloss GEBÜHR mit 4711 Stimmen.", quellen="Quelle: Protokoll")
    assert sent == []


def test_cold_prompt_without_hidden_terms_is_sent():
    sent = []
    result = vc.check_contamination(
        "Musterstadt 2021", llm=lambda model, prompt: sent.append(prompt) or "weiß nicht",
        material="Ausgangslage ohne Details.", topic="Parkgebühren",
        hidden_outcomes=[{"text_de": "Frage?", "quelle": "Bericht vom 12.03.2022"}],
        verlauf="Am 12.03.2022 beschloss der Rat.", quellen="Quelle")
    assert sent
    assert result["known"] is False


def test_year_in_case_label_is_not_a_leak():
    sent = []
    vc.check_contamination(
        "Musterstadt 2021", llm=lambda model, prompt: sent.append(prompt) or "",
        material="Ausgangslage.", topic="Parkgebühren", hidden_outcomes=[],
        verlauf="Im Jahr 2021 beschloss der Rat.", quellen="Quelle")
    assert sent
