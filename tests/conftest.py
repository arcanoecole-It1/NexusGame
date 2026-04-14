"""
conftest.py — NexusGame Test Suite
====================================
Fixtures partagées entre tous les modules de test.
"""
import pytest
import tempfile
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import app_gamestore as gs


# ── Fixtures Flask ────────────────────────────────────────────────────────────

@pytest.fixture()
def app():
    """
    Application Flask configurée pour les tests.
    Utilise une BDD temporaire isolée (tempfile) — une BDD fraîche par test.
    """
    db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db_path = db_file.name
    db_file.close()

    gs.app.config.update({
        "TESTING": True,
        "DATABASE": db_path,
        "PROPAGATE_EXCEPTIONS": False,
    })

    gs.init_db(db_path)

    yield gs.app

    os.unlink(db_path)


@pytest.fixture()
def client(app):
    """Client de test Flask — utilisé pour les tests unitaires et d'intégration."""
    return app.test_client()


# ── Fixtures partagées pour les tests unitaires

@pytest.fixture()
def sample_game():
    """Fixture : dictionnaire d'un jeu valide complet."""
    return {
        'title': 'Baldur\'s Gate 3',
        'genre': 'RPG',
        'price': 59.99,
        'rating': 4.9,
        'stock': 150,
        'publisher': 'Larian Studios',
        'year': 2023
    }


@pytest.fixture()
def sample_game_minimal():
    """Fixture : jeu minimaliste (champs obligatoires seulement)."""
    return {
        'title': 'Minimal Game',
        'genre': 'Action',
        'price': 19.99
    }


@pytest.fixture()
def created_game(client, sample_game):
    """Fixture : crée un jeu en BD et retourne sa réponse complète."""
    response = client.post('/games', json=sample_game, content_type='application/json')
    assert response.status_code == 201
    return response.get_json()


# ── Fixtures Playwright ───────────────────────────────────────────────────────

def pytest_configure(config):
    config.addinivalue_line("markers", "slow: tests lents (>1s)")
    config.addinivalue_line("markers", "ui: tests Playwright")
    config.addinivalue_line("markers", "integration: tests d'intégration")
    config.addinivalue_line("markers", "unit: tests unitaires")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, "rep_" + rep.when, rep)


@pytest.fixture(autouse=False)
def screenshot_on_fail(page, request):
    """Capture automatique en cas d'échec Playwright."""
    yield
    if hasattr(request.node, "rep_call") and request.node.rep_call.failed:
        os.makedirs("screenshots", exist_ok=True)
        page.screenshot(path=f"screenshots/{request.node.name}.png")
