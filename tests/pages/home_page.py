"""
pages/home_page.py — Page Object : page d'accueil GameStore
=============================================================
Centralise tous les sélecteurs et actions de la page principale.
Les tests ne doivent JAMAIS écrire de sélecteur directement —
tout passe par cette classe.
"""
from playwright.sync_api import Page

BASE_URL = "http://localhost:5000"


class HomePage:

    def __init__(self, page: Page):
        self.page = page

        # Locators pour chaque élément interactif
        self.game_list = page.locator('[data-testid="game-list"]')
        self.game_count = page.locator('#game-count')
        self.add_btn = page.locator('[data-testid="add-game-btn"]')
        self.search_input = page.locator('[data-testid="search-input"]')
        self.genre_filter = page.locator('[data-testid="genre-filter"]')
        self.game_cards = page.locator('[data-testid="game-card"]')

    def navigate(self):
        """Naviguer vers la page d'accueil."""
        self.page.goto(BASE_URL)

    def get_game_cards(self):
        """Retourner le locator de toutes les cartes de jeux."""
        return self.game_cards

    def get_game_count_text(self) -> str:
        """Retourner le texte du compteur de jeux."""
        return self.game_count.text_content()

    def open_add_form(self):
        """Cliquer sur le bouton Ajouter un jeu."""
        self.add_btn.click()

    def search(self, query: str):
        """Taper une requête dans la barre de recherche."""
        self.search_input.fill(query)

    def filter_genre(self, genre: str):
        """Sélectionner un genre dans le filtre déroulant."""
        self.genre_filter.select_option(genre)

    def filter_name(self, name: str):
        """Filtrer par nom (via la barre de recherche)."""
        self.search_input.fill(name)

    def click_game_card(self, index: int = 0):
        """Cliquer sur une carte de jeu (par défaut la première)."""
        self.game_cards.nth(index).click()

    def is_on_home_page(self) -> bool:
        """Vérifier qu'on est sur la page d'accueil (présence du bouton ajouter)."""
        return self.add_btn.is_visible()
