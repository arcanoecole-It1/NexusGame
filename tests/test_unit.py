"""
test_unit.py — Tests unitaires NexusGame
==========================================
Contexte : Suite de tests unitaires sur l'API GameStore.
Chaque test est isolé — BDD fraîche à chaque appel (fixture function scope).
Lancement :
    pytest tests/test_unit.py -v
    pytest tests/test_unit.py -v --cov=app_gamestore --cov-report=html
"""
import pytest


# ════════════════════════════════════════════════════════════════════════════════
# SECTION 1 — Health & endpoints de base
# ════════════════════════════════════════════════════════════════════════════════

class TestHealth:
    def test_health_retourne_200(self, client):
        """Vérifier que GET /health retourne 200 OK."""
        response = client.get('/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data is not None

    def test_health_contient_service(self, client):
        """Vérifier que la réponse contient la clé 'service'."""
        response = client.get('/health')
        data = response.get_json()
        assert 'service' in data
        assert data['service'] == 'GameStore API'


# ════════════════════════════════════════════════════════════════════════════════
# SECTION 2 — Liste des jeux
# ════════════════════════════════════════════════════════════════════════════════

class TestListGames:
    def test_liste_retourne_200(self, client):
        """GET /games retourne 200 et une liste non vide."""
        response = client.get('/games')
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_liste_contient_les_champs_attendus(self, client):
        """Chaque jeu retourné contient : id, title, genre, price, rating."""
        response = client.get('/games')
        games = response.get_json()
        for game in games:
            assert 'id' in game
            assert 'title' in game
            assert 'genre' in game
            assert 'price' in game
            assert 'rating' in game

    def test_filtre_par_genre(self, client):
        """GET /games?genre=RPG retourne uniquement des jeux RPG."""
        response = client.get('/games?genre=RPG')
        assert response.status_code == 200
        games = response.get_json()
        assert len(games) > 0
        for game in games:
            assert game['genre'] == 'RPG'

    def test_tri_par_prix_croissant(self, client):
        """GET /games?sort=price&order=asc retourne jeux triés par prix croissant."""
        response = client.get('/games?sort=price&order=asc')
        assert response.status_code == 200
        games = response.get_json()
        prices = [game['price'] for game in games]
        assert prices == sorted(prices)


# ════════════════════════════════════════════════════════════════════════════════
# SECTION 3 — Création de jeux
# ════════════════════════════════════════════════════════════════════════════════

class TestCreateGame:
    def test_creation_valide_retourne_201(self, client, sample_game):
        """POST /games avec données valides → 201 avec id."""
        response = client.post('/games', json=sample_game, content_type='application/json')
        assert response.status_code == 201
        data = response.get_json()
        assert 'id' in data
        assert data['id'] > 0
        assert data['title'] == sample_game['title']

    def test_creation_sans_titre_retourne_400(self, client):
        """POST /games sans 'title' → 400."""
        payload = {'genre': 'RPG', 'price': 49.99}
        response = client.post('/games', json=payload)
        assert response.status_code == 400

    def test_creation_prix_negatif_retourne_400(self, client):
        """POST /games avec price = -5 → 400."""
        payload = {'title': 'Test', 'genre': 'RPG', 'price': -10}
        response = client.post('/games', json=payload)
        assert response.status_code == 400

    def test_creation_titre_duplique_retourne_409(self, client, sample_game):
        """Créer le même jeu deux fois → second appel retourne 409."""
        response1 = client.post('/games', json=sample_game)
        assert response1.status_code == 201
        response2 = client.post('/games', json=sample_game)
        assert response2.status_code == 409

    @pytest.mark.parametrize("payload,expected_status", [
        ({'genre': 'RPG', 'price': 49.99}, 400),  # Manque title
        ({'title': 'Test', 'price': 49.99}, 400),  # Manque genre
        ({'title': 'Test', 'genre': 'RPG'}, 400),  # Manque price
        ({'title': 'Test', 'genre': 'RPG', 'price': 'abc'}, 400),  # Price non-num
        ({'title': 'Test', 'genre': 'RPG', 'price': 49.99, 'rating': 6}, 400),  # Rating > 5
        ({'title': 'Test', 'genre': 'RPG', 'price': 49.99, 'stock': -5}, 400),  # Stock < 0
    ])
    def test_validation_parametree(self, client, payload, expected_status):
        """POST /games avec divers payloads, vérifier status code."""
        response = client.post('/games', json=payload)
        assert response.status_code == expected_status


# ════════════════════════════════════════════════════════════════════════════════
# SECTION 4 — Récupération, mise à jour, suppression
# ════════════════════════════════════════════════════════════════════════════════

class TestGameCRUD:
    def test_get_jeu_existant(self, client, created_game):
        """GET /games/{id} pour jeu existant → 200."""
        game_id = created_game['id']
        response = client.get(f'/games/{game_id}')
        assert response.status_code == 200
        data = response.get_json()
        assert data['id'] == game_id

    def test_get_jeu_inexistant_retourne_404(self, client):
        """GET /games/99999 (inexistant) → 404."""
        response = client.get('/games/99999')
        assert response.status_code == 404

    def test_update_prix(self, client, created_game):
        """PUT /games/{id} avec nouveau prix → 200 et mise à jour."""
        game_id = created_game['id']
        payload = {'price': 29.99}
        response = client.put(f'/games/{game_id}', json=payload)
        assert response.status_code == 200
        data = response.get_json()
        assert data['price'] == 29.99

    def test_delete_jeu(self, client, created_game):
        """DELETE /games/{id} → 204, puis GET → 404."""
        game_id = created_game['id']
        response1 = client.delete(f'/games/{game_id}')
        assert response1.status_code == 204
        response2 = client.get(f'/games/{game_id}')
        assert response2.status_code == 404


# ════════════════════════════════════════════════════════════════════════════════
# SECTION 5 — Choix libres (à justifier dans le README)
# ════════════════════════════════════════════════════════════════════════════════

class TestChoixLibres:
    """Tests supplémentaires pour cas critiques et edge cases."""
    
    def test_update_inexistant_retourne_404(self, client):
        """PUT /games/99999 (inexistant) → 404."""
        payload = {'price': 29.99}
        response = client.put('/games/99999', json=payload)
        assert response.status_code == 404
    
    def test_delete_inexistant_retourne_404(self, client):
        """DELETE /games/99999 (inexistant) → 404."""
        response = client.delete('/games/99999')
        assert response.status_code == 404
    
    def test_creation_prix_zero_valide(self, client):
        """POST /games avec price = 0 (jeu gratuit) → 201."""
        payload = {'title': 'Free Game', 'genre': 'FPS', 'price': 0}
        response = client.post('/games', json=payload)
        assert response.status_code == 201
        data = response.get_json()
        assert data['price'] == 0
    
    def test_update_titre_duplique_retourne_409(self, client, sample_game):
        """PUT avec titre déjà utilisé ailleurs → 409."""
        # Créer deux jeux
        payload1 = {'title': 'Game A', 'genre': 'RPG', 'price': 49.99}
        payload2 = {'title': 'Game B', 'genre': 'Action', 'price': 39.99}
        r1 = client.post('/games', json=payload1)
        r2 = client.post('/games', json=payload2)
        game1_id = r1.get_json()['id']
        game2_id = r2.get_json()['id']
        # Essayer de renommer game2 avec le titre de game1
        response = client.put(f'/games/{game2_id}', json={'title': 'Game A'})
        assert response.status_code == 409
    
    def test_creation_prix_non_numerique_retourne_400(self, client):
        """POST /games avec price non-numérique → 400."""
        payload = {'title': 'Test', 'genre': 'RPG', 'price': 'invalid'}
        response = client.post('/games', json=payload)
        assert response.status_code == 400
    
    def test_update_prix_invalide_retourne_400(self, client, created_game):
        """PUT /games/{id} avec price invalide → 400."""
        game_id = created_game['id']
        response = client.put(f'/games/{game_id}', json={'price': -10})
        assert response.status_code == 400


# ════════════════════════════════════════════════════════════════════════════════
# SECTION 6 — Endpoint /games/featured (NGS-108)
# ════════════════════════════════════════════════════════════════════════════════

class TestFeatured:
    """
    Tests sur l'endpoint GET /games/featured.
    Consultez la documentation de l'endpoint dans app_gamestore.py.
    Si un test échoue alors que votre assertion est correcte,
    documentez ce que vous observez dans le README.
    """

    def test_featured_retourne_200(self, client):
        """TODO — GET /games/featured retourne 200."""
        pass

    def test_featured_retourne_liste(self, client):
        """TODO — La réponse contient une clé 'featured' qui est une liste."""
        pass

    def test_featured_max_5_par_defaut(self, client):
        """TODO — Sans paramètre, au maximum 5 jeux sont retournés."""
        pass

    def test_featured_limit_param(self, client):
        """TODO — ?limit=3 retourne au maximum 3 jeux."""
        pass

    def test_featured_tries_par_rating_decroissant(self, client):
        """TODO — Les jeux sont triés par rating décroissant."""
        pass

    def test_featured_sans_jeux_gratuits(self, client):
        """TODO — Les jeux gratuits ne doivent pas apparaître dans featured."""
        pass

    def test_featured_sans_jeux_hors_stock(self, client):
        """TODO — Les jeux hors stock ne doivent pas apparaître dans featured."""
        pass
