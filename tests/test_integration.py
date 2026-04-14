"""
test_integration.py — Tests d'intégration NexusGame
=====================================================
Tests de bout en bout sur l'API GameStore avec un serveur réel.
Ces tests valident le comportement complet, pas seulement la logique unitaire.

Lancement :
    pytest tests/test_integration.py -v -m integration
    pytest tests/test_integration.py -v --html=reports/integration.html
"""
import pytest
import requests
import time
import sys
import os
import subprocess
import threading

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ════════════════════════════════════════════════════════════════════════════════
# FIXTURE — Serveur GameStore en processus réel
# ════════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def api_url():
    """
    Démarre l'API GameStore en sous-processus réel,
    attend qu'elle soit prête, puis la stoppe après les tests.
    """
    # Démarrer le serveur en subprocess
    proc = subprocess.Popen(
        [sys.executable, "app_gamestore.py"],
        cwd=os.path.dirname(__file__),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Attendre que le serveur soit prêt (timeout 10s)
    base_url = "http://localhost:5000"
    for _ in range(20):  # 20 tentatives x 0.5s = 10s max
        try:
            response = requests.get(f"{base_url}/health", timeout=1)
            if response.status_code == 200:
                break
        except requests.exceptions.RequestException:
            pass
        time.sleep(0.5)
    else:
        proc.terminate()
        proc.wait()
        pytest.fail("Serveur n'a pas démarré dans les 10 secondes")
    
    yield base_url
    
    # Nettoyer : arrêter le serveur
    proc.terminate()
    proc.wait()


# ════════════════════════════════════════════════════════════════════════════════
# SECTION 1 — Scénarios de bout en bout
# ════════════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestScenariosCatalogueComplet:
    """
    Scénarios E2E sur le catalogue de jeux.
    """

    def test_catalogue_initial_non_vide(self, api_url):
        """GET /games retourne 200 et une liste non vide."""
        response = requests.get(f"{api_url}/games")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_cycle_complet_creation_lecture_suppression(self, api_url):
        """
        Scénario complet :
        1. POST /games → créer un jeu, récupérer son id
        2. GET /games/{id} → vérifier qu'il existe
        3. DELETE /games/{id} → supprimer
        4. GET /games/{id} → vérifier 404
        """
        # 1. Créer un jeu
        payload = {
            'title': 'Integration Test Game',
            'genre': 'RPG',
            'price': 49.99
        }
        response = requests.post(f"{api_url}/games", json=payload)
        assert response.status_code == 201
        game_data = response.json()
        game_id = game_data['id']
        
        # 2. Récupérer le jeu créé
        response = requests.get(f"{api_url}/games/{game_id}")
        assert response.status_code == 200
        retrieved = response.json()
        assert retrieved['id'] == game_id
        assert retrieved['title'] == payload['title']
        
        # 3. Supprimer le jeu
        response = requests.delete(f"{api_url}/games/{game_id}")
        assert response.status_code == 204
        
        # 4. Vérifier qu'il n'existe plus
        response = requests.get(f"{api_url}/games/{game_id}")
        assert response.status_code == 404

    def test_mise_a_jour_stock(self, api_url):
        """
        Créer un jeu avec stock=10, PUT pour passer à stock=0,
        vérifier que la valeur est bien persistée en base.
        """
        # Créer un jeu avec stock initial
        payload = {
            'title': 'Stock Test Game',
            'genre': 'Action',
            'price': 39.99,
            'stock': 10
        }
        response = requests.post(f"{api_url}/games", json=payload)
        assert response.status_code == 201
        game_id = response.json()['id']
        
        # Mettre à jour le stock à 0
        update_payload = {'stock': 0}
        response = requests.put(f"{api_url}/games/{game_id}", json=update_payload)
        assert response.status_code == 200
        updated = response.json()
        assert updated['stock'] == 0
        
        # Vérifier que la mise à jour persiste (relecture)
        response = requests.get(f"{api_url}/games/{game_id}")
        assert response.status_code == 200
        final = response.json()
        assert final['stock'] == 0


# ════════════════════════════════════════════════════════════════════════════════
# SECTION 2 — Tests de robustesse
# ════════════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestRobustesse:
    """
    Ces tests valident le comportement de l'API sous des conditions inhabituelles.
    """

    def test_requetes_concurrentes(self, api_url):
        """
        Envoyer 10 requêtes GET /games en parallèle avec threading.
        Vérifier que toutes retournent 200.
        """
        results = []
        errors = []
        
        def make_request():
            try:
                response = requests.get(f"{api_url}/games", timeout=5)
                results.append(response.status_code)
            except Exception as e:
                errors.append(str(e))
        
        # Lancer 10 threads en parallèle
        threads = [threading.Thread(target=make_request) for _ in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        # Vérifier les résultats
        assert len(errors) == 0, f"Erreurs dans les requêtes concurrentes: {errors}"
        assert len(results) == 10, f"Seulement {len(results)} requêtes réussies sur 10"
        assert all(status == 200 for status in results), f"Statuts reçus: {results}"

    def test_payload_json_malforme(self, api_url):
        """
        POST /games avec un body non-JSON (texte brut).
        L'API doit retourner 400 sans crasher.
        """
        headers = {'Content-Type': 'text/plain'}
        response = requests.post(f"{api_url}/games", 
                               data="ceci n'est pas du json",
                               headers=headers)
        # L'API devrait retourner 400 pour body non-JSON
        assert response.status_code == 400


# ════════════════════════════════════════════════════════════════════════════════
# SECTION 3 — Choix libres (à justifier dans le README)
# ════════════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestChoixLibresIntegration:
    """
    Scénarios d'intégration critiques :
    - Workflow de recherche et filtrage complet
    - Gestion des erreurs réseau simulées
    - Validation de la persistance des données après redémarrage
    """
    
    def test_workflow_recherche_complete(self, api_url):
        """
        Scénario complet de recherche :
        1. Créer plusieurs jeux de genres différents
        2. Tester les filtres par genre
        3. Tester le tri par prix
        4. Vérifier que les résultats sont cohérents
        """
        # Créer des jeux de test
        games = [
            {'title': 'RPG Game', 'genre': 'RPG', 'price': 59.99},
            {'title': 'Action Game', 'genre': 'Action', 'price': 39.99},
            {'title': 'Strategy Game', 'genre': 'Strategy', 'price': 49.99}
        ]
        
        created_ids = []
        for game in games:
            response = requests.post(f"{api_url}/games", json=game)
            assert response.status_code == 201
            created_ids.append(response.json()['id'])
        
        # Tester le filtre RPG
        response = requests.get(f"{api_url}/games?genre=RPG")
        assert response.status_code == 200
        rpg_games = response.json()
        assert len(rpg_games) >= 1  # Au moins notre jeu créé
        assert all(g['genre'] == 'RPG' for g in rpg_games)
        
        # Tester le tri par prix croissant
        response = requests.get(f"{api_url}/games?sort=price&order=asc")
        assert response.status_code == 200
        sorted_games = response.json()
        prices = [g['price'] for g in sorted_games]
        assert prices == sorted(prices)
        
        # Nettoyer les jeux créés
        for game_id in created_ids:
            requests.delete(f"{api_url}/games/{game_id}")

    def test_validation_erreurs_consecutives(self, api_url):
        """
        Tester que l'API reste stable après plusieurs erreurs consécutives.
        """
        # Envoyer plusieurs requêtes invalides
        invalid_payloads = [
            {},  # Vide
            {'genre': 'RPG'},  # Manque title et price
            {'title': 'Test'},  # Manque genre et price
            {'title': 'Test', 'genre': 'RPG', 'price': -10},  # Price négatif
        ]
        
        for payload in invalid_payloads:
            response = requests.post(f"{api_url}/games", json=payload)
            assert response.status_code == 400
        
        # Vérifier que l'API fonctionne encore après les erreurs
        response = requests.get(f"{api_url}/health")
        assert response.status_code == 200
        
        # Et qu'on peut créer un jeu valide
        valid_payload = {'title': 'Valid After Errors', 'genre': 'RPG', 'price': 29.99}
        response = requests.post(f"{api_url}/games", json=valid_payload)
        assert response.status_code == 201
