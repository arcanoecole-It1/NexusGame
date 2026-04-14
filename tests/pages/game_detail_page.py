"""
pages/game_detail_page.py — Page Object : page détail d'un jeu
===============================================================
Encapsule les interactions avec la page de détail d'un jeu.
(Note: Dans cette implémentation single-page, la "détail" est simulée.)
"""
from playwright.sync_api import Page


class GameDetailPage:

    def __init__(self, page: Page):
        self.page = page

        # Pour une single-page app, pas de page détail séparée

    def is_detail_view(self) -> bool:
        """Vérifier si on est en vue détail (placeholder pour single-page)."""
        # Puisque c'est single-page, retourner True si on est sur la home
        return self.page.url == "http://localhost:5000/"

    def go_back(self):
        """Revenir en arrière."""
        self.page.go_back()