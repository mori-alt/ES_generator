from scrapers.Scraper import Scraper  # 1で作成したファイル名に合わせて変更
import requests
import time

class LoginScraper(Scraper):
    def __init__(self, login_url, home_url, credentials):
        super().__init__(home_url)
        self.login_url = login_url
        self.credentials = credentials
        self.session = requests.Session()
        self.set_login_info()
        self.is_logged_in = False

    # ウェブサイト毎に与えるべき情報が違うと考えられるためここだけ変更して対応できるようにコンストラクタから外してる
    # 分からなくなるからコンストラクタ以外で呼び出さないこと 書いてて思ったけどコンストラクタのオーバーライドと何が違うのでしょう審議
    def set_login_info(self):
        self.login_info = None
        raise NotImplementedError("This method should be overridden by the child class")

    def login(self):
        if not self.is_logged_in:
            try:
                # ログインページに対して必要な情報をポストする
                response = self.session.post(self.login_url, data=self.login_info)
                response.raise_for_status()  # 200番台ならログイン成功らしいです
            except requests.RequestException as e:
                print(f"Error occurred during login: {e}")
                return False
            else:
                self.is_logged_in = True
                time.sleep(5)
                return True
        return True

    # ページ全体のドキュメントを取得する
    def get_page_html(self):
        if not self.is_logged_in and not self.login():
            print("Login failed.")
            return None
        try:
            response = self.session.get(self.url)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Error occurred: {e}")
            return None
        else:
            time.sleep(5)
            return response.text