"""
pages/add_game_modal.py — Page Object : modal d'ajout de jeu
"""
from playwright.sync_api import Page, expect


class AddGameModal:

    def __init__(self, page: Page):
        self.page = page
        self.modal      = page.locator('[data-testid="add-game-modal"]')
        self.input_title  = page.locator('[data-testid="input-title"]')
        self.input_genre  = page.locator('[data-testid="input-genre"]')
        self.input_price  = page.locator('[data-testid="input-price"]')
        self.input_rating = page.locator('[data-testid="input-rating"]')
        self.input_stock  = page.locator('[data-testid="input-stock"]')
        self.input_year   = page.locator('[data-testid="input-year"]')
        self.submit_btn   = page.locator('[data-testid="submit-btn"]')
        self.cancel_btn   = page.locator('[data-testid="cancel-btn"]')

    def wait_until_open(self):
        """Attendre que le modal soit visible avant toute interaction."""
        self.page.wait_for_selector(
            '[data-testid="add-game-modal"].open',  # la classe .open est ajoutée par openModal()
            state="visible",
            timeout=5000
        )

    def fill_and_submit(self, title: str, genre: str, price: float,
                        rating: float = None, stock: int = None, year: int = None):
        # ✅ Attendre que le modal soit ouvert AVANT de fill
        self.wait_until_open()

        self.input_title.fill(title)
        self.input_genre.fill(genre)
        self.input_price.fill(str(price))
        if rating is not None:
            self.input_rating.fill(str(rating))
        if stock is not None:
            self.input_stock.fill(str(stock))
        if year is not None:
            self.input_year.fill(str(year))
        self.submit_btn.click()

    def cancel(self):
        self.cancel_btn.click()

    def is_visible(self) -> bool:
        return self.modal.is_visible()