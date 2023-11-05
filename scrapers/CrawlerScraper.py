from scrapers.LoginScraper import LoginScraper  # 2で作成したファイル名に合わせて変更
import time
from bs4 import BeautifulSoup

class CrawlerScraper(LoginScraper):
    def __init__(self, login_url, home_url, credentials):
        super().__init__(login_url, home_url, credentials)
        self.visited = set()  # To track which pages have already been visited

    # ページ内の下位リンクを取得
    def find_sub_links_info(self, soup):
        """
                This function should be overridden by any class that inherits from Scraper.
                """
        raise NotImplementedError("This method should be overridden by the child class")

    # 次のページへのリンクを探す
    def find_next_link(self, soup):
        """
                This function should be overridden by any class that inherits from Scraper.
                """
        raise NotImplementedError("This method should be overridden by the child class")

    # 処理を回す
    def crawl(self, url):
        print('start crawl')
        # 探索するURLを設定、重複防止集合に追加
        self.url = url
        self.visited.add(url)

        html = self.get_page_html()
        if html is None:
            return []

        # ドキュメント全体を解析してsoupクラスに変換
        soup = BeautifulSoup(html, 'html.parser')
        print('get sub links')
        sub_links = self.find_sub_links_info(soup)

        # 情報取得先のページに応じて処理を行う
        for link in sub_links:
            if link not in self.visited:
                self.url = link
                page_html = self.get_page_html()
                time.sleep(5)
                if page_html is not None:
                    print('parse page')
                    self.parse_page(page_html)
                self.visited.add(link)

        # 次のページに対して処理を行う
        next_link = self.find_next_link(soup)
        if next_link and next_link not in self.visited:
            print('next page')
            self.crawl(next_link)