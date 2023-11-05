import requests
import time


class Scraper:
    def __init__(self, url):
        self.url = url

    # ページのドキュメントの取得
    def get_page_html(self):
        try:
            response = requests.get(self.url)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Error occurred: {e}")
            return None
        else:
            time.sleep(5)
            return response.text

    # ページの解析
    def parse_page(self, html):
        """
        This function should be overridden by any class that inherits from Scraper.
        """
        raise NotImplementedError("This method should be overridden by the child class")

    # スクレイピングの処理全体
    def scrape(self):
        html = self.get_page_html()
        if html is not None:
            return self.parse_page(html)
        else:
            return None
