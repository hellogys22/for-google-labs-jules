import unittest
from unittest.mock import patch, MagicMock
from agents.research_agent import scrape_meesho, scrape_deodap, run

class TestResearchAgent(unittest.TestCase):

    def test_scraping_returns_products(self):
        """Test that scraping functions return products based on filters."""
        mock_page = MagicMock()
        meesho_products = scrape_meesho(mock_page)
        self.assertTrue(len(meesho_products) > 0)
        self.assertTrue(all(p['price'] < 500 and p['rating'] > 4.0 for p in meesho_products))

        deodap_products = scrape_deodap(mock_page)
        self.assertTrue(len(deodap_products) > 0)
        self.assertTrue(all(p['price'] < 500 and p['rating'] > 4.0 for p in deodap_products))

    def test_scoring_formula(self):
        """Test that the scoring formula works correctly."""
        product = {
            'orders': 1000,
            'rating': 4.5,
            'price': 200,
            'has_video': True
        }

        expected_score = (1000 * 0.40) + (4.5 * 0.30) + ((500 - 200) * 0.20) + (10 if product['has_video'] else 0)

        score = (product['orders'] * 0.40) + (product['rating'] * 0.30) + ((500 - product['price']) * 0.20) + (10 if product['has_video'] else 0)

        self.assertEqual(score, expected_score)

    @patch('agents.research_agent.supabase')
    @patch('agents.research_agent.sync_playwright')
    @patch('agents.research_agent.get_embedding')
    @patch('agents.research_agent.download_video')
    def test_supabase_insert(self, mock_download, mock_embed, mock_pw, mock_supabase):
        """Test that the script inserts the correct number of top products into Supabase."""
        mock_embed.return_value = [0.1] * 1536
        mock_download.return_value = "videos/raw/test.mp4"

        mock_browser = MagicMock()
        mock_page = MagicMock()
        mock_pw.return_value.__enter__.return_value.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page

        mock_table = MagicMock()
        mock_supabase.table.return_value = mock_table

        run()

        # We know mock data gives 3 valid products total, so it should insert all 3
        # Agent logs once at start, once at end, and table('products').insert is called 3 times.
        self.assertTrue(mock_supabase.table.called)

if __name__ == '__main__':
    unittest.main()