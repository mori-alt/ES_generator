from scrapers.CrawlerScraper import CrawlerScraper
import time
import pathlib
import re
import json
import os
from bs4 import BeautifulSoup
from urllib.parse import urljoin


class OneCareerScraper(CrawlerScraper):
    def __init__(self, login_url, home_url, credentials):
        super().__init__(login_url, home_url, credentials)
        self.home_dir_path = "./res/ES_scraping"

    def set_login_info(self):
        # get csrf token
        time.sleep(5)
        response = self.session.get(self.login_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        csrf_token = soup.find('meta', {'name': 'csrf-token'})['content']
        if csrf_token is None:
            print('Unable to find meta with name csrf-token')
            return None

        # こいつの処理はいい感じにしたい　今のままだとなんか変
        self.login_info = {
            'user[email]': self.credentials['username'],
            'user[password]': self.credentials['password'],
            'authenticity_token': csrf_token
        }

    # 下位ページのリンクとディレクトリ作成用の情報を取得する
    def find_sub_links_info(self, soup):
        print('Find sub links')
        experience_item_div = soup.find_all('div', {'class': 'v2-experiences__item'})
        sub_links_info = []

        # 'div', {'class': 'v2-experiences__item'}　このタグを持つ要素の中で情報を取得する
        for item in experience_item_div:
            # 会社名の取得
            company_name_text = item.find('h3', {'class': 'v2-experiences__company-name'}).get_text().replace('\n', '').replace('　', '').replace('/', '').replace('\\', '').strip()
            # 事業分野の取得
            job_category_text = item.find('div', {'class': 'v2-experiences__job-category'}).get_text().replace('\n', '').replace('　', '').replace('/', '').replace('\\', '').strip()
            # 卒業年度の取得
            graduate_year_text = item.find('div', {'class': 'v2-experiences__graduate-year'}).get_text().replace('\n', '').replace('　', '').replace('/', '').replace('\\', '').strip()
            # 大学情報の取得
            university_text = item.find('div', {'class': 'v2-experiences__published-profile'}).get_text().replace('\n', '').replace('　', '').replace('/', '').replace('\\', '').strip()

            # 内定しているかどうかの取得
            offer_content = item.find('div', {'class': 'v2-experience__qualified'})
            if offer_content is None:
                is_offer = 0
            elif '内定' in offer_content.get_text():
                is_offer = 1
            else:
                is_offer = 2  # ここにはインターン選考の通過も含まれる

            # 選考タイプの判定
            selection_type_content = item.find('div', {'class': 'v2-experiences__large-category'})
            if selection_type_content is None:
                selection_type = 0
            elif '本選考' in selection_type_content.get_text():
                selection_type = 1
            elif 'インターン' in selection_type_content.get_text():
                selection_type = 2
            else:
                selection_type = 0

            # ページタイプの指定
            page_type_content = item.find('div', {'class': 'v2-experiences__middle-category'})
            if 'ES' in page_type_content.get_text() or 'エントリーシート' in page_type_content.get_text():
                page_type = 1
            elif '面接' in page_type_content.get_text():
                page_type = 2
            else:
                page_type = 0

            # URLの取得
            sub_url = item.find('a').get('href')
            sub_url = urljoin(self.url, sub_url)

            # ページのURLと内定、選考タイプ、ESか面接かを保存する
            page_info = {
                'company_name': company_name_text,
                'job_category': job_category_text,
                'graduate_year': graduate_year_text,
                'university': university_text,
                'offer': is_offer,
                'selection_type': selection_type,
                'page_type': page_type,
                'URL': sub_url
            }
            sub_links_info.append(page_info)
            print(page_info)

        return sub_links_info

    def find_next_link(self, soup):
        one_career_url = 'https://www.onecareer.jp'
        li = soup.find('li', {'class': 'v2-pagination__next'})

        if li is not None:
            link = li.find('a').get('href')
            if link is None:
                print('Unable to find a in this li')
                return None

            return urljoin(one_career_url, link)

        else:
            print('This is last page')
            print('Finished scraping')
            return None

    # ページの内容保存
    # fixme 引数が継承元と違うの良くなさそうなのでいい感じに対応を考えること
    def parse_page(self, html):
        print('Parse page')
        soup = BeautifulSoup(html, 'html.parser')

        if self.is_page_es(soup):
            qa_pairs = self.make_qa_pairs_from_ES_page(soup)
            return qa_pairs
        else:
            print('this page is not ES in parse')
            return None  # json_dataを返す関数だけどこの関数の呼び出し前にページ内容の判定はしているからNoneを返しても問題ないはず。でもあとでいい感じにしたい

    def make_responder_from_page_info(self, page_info):
        # page_infoの中身で数値のものを意味のある文字列に変換する
        # todo この処理はあくまで一時的なものだと思う　crawlの中の条件分岐をいい感じに変換できるならこれはいらないかも
        if page_info['selection_type'] == 1:
            selection_type = 'final_selections'
        elif page_info['selection_type'] == 2:
            selection_type = 'internship_selections'
        else:
            selection_type = 'others'

        if page_info['offer'] == 1:
            offer = 'offered'
        elif page_info['offer'] == 2:
            offer = 'others'  # これにはインターン選考の通過がはいることを留意
        else:
            offer = 'nothings'

        responder = {
                     'company_name': page_info['company_name'],
                     'job_category': page_info['job_category'],
                     'graduate_year': page_info['graduate_year'],
                     'university': page_info['university'],
                     'selection_type': selection_type,
                     'offer': offer,
                     'URL': page_info['URL'],
                     'page_type': 'ES'
                     }

        return responder

    # サブリンクで取得したページの中から必要な情報をjson形式に変換する
    @staticmethod
    def make_qa_pairs_from_ES_page(soup):
        # このタグには設問と回答が含まれている
        div = soup.find('div', {'class': 'v2-curriculum-item-body__content'})
        if div is None:
            print('Unable to find div with class v2-curriculum-item-body__content')
            return None

        # h3タグとpタグの内容を抽出
        qa_pairs = []
        for h3 in div.find_all('h3'):
            question = h3.get_text()
            answer = h3.find_next_sibling('p').get_text()
            qa_pairs.append({"question": question, "answer": answer})
            print(question)
            print(answer)

        return qa_pairs

    @staticmethod
    def extract_numbers_from_url(url: str) -> str:
        # 正規表現を使用してURLから数値を抽出
        numbers = re.findall(r'(\d+)', url)

        # 最後の2つの数値を取得してフォーマット
        formatted_result = f"{numbers[-2]}-{numbers[-1]}"
        return formatted_result


    def get_classification(self, json_data):
        university = json_data['responder']['university']
        if '文系' in university:
            return 'LiberalArts'
        elif '理系' in university:
            return 'Sciences'
        else:
            return 'Others'

    def make_json_path(self, json_data):
        file_name = json_data['responder']['job_category'] + self.extract_numbers_from_url(json_data['responder']['URL']) + '.json'
        output_dir = os.path.join(self.home_dir_path, json_data['responder']['company_name'], self.get_classification(json_data), json_data['responder']['graduate_year'], json_data['responder']['selection_type'], json_data['responder']['offer'], ' ')
        dir_path = pathlib.Path(output_dir)
        dir_path.mkdir(parents=True, exist_ok=True)

        output_path = output_dir + file_name
        return output_path

    def save_json_data(self, json_data):
        output_path = self.make_json_path(json_data)
        print('save: ', output_path)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)

    # sub_linksの返り値を辞書型にする変更をしてる
    def crawl(self, url):
        # URLを取得してダブり防止用のリストに追加
        print('start crawl')
        self.url = url
        self.visited.add(url)

        # ページ全体のHTMLを取得する
        html = self.get_page_html()
        if html is None:
            print('This page is None')

        # ドキュメント全体を解析してsoupクラスに変換
        soup = BeautifulSoup(html, 'html.parser')

        # ページ内の要素の取得
        sub_pages_info = self.find_sub_links_info(soup)
        for page_info in sub_pages_info:
            # Skip if page is not of type 1 (ES)
            if page_info['page_type'] != 1:
                print('This page is not ES')
                continue

            # Skip if the URL is already visited
            if page_info['URL'] in self.visited:
                print('This URL has already visited')
                continue

            # Set the URL and get HTML
            self.url = page_info['URL']
            page_html = self.get_page_html()
            time.sleep(5)

            # scrape page contents
            if page_html is not None:
                qa_pairs = self.parse_page(page_html)
                responder = self.make_responder_from_page_info(page_info)
                json_data = {
                    "responder": responder,
                    "qa_pairs": qa_pairs,
                }
                self.save_json_data(json_data)
            else:
                print('page_html is None')

            self.visited.add(page_info['URL'])

        # 次のページに対して処理を行う
        next_link = self.find_next_link(soup)
        if next_link and next_link not in self.visited:
            print('next page')
            self.crawl(next_link)

    @staticmethod
    def is_page_es(soup):
        header = soup.find('div', {'class': 'v2-experience-header__middle-category'})
        if header is None:
            print('Unable to find div with class v2-experience-header__middle-category')
            return False  # Noneを返すか迷ってるけど、Noneにすると呼び出しもとの条件分岐変になりそうだからFalseを返すことにした

        if 'ES' in header.string or 'エントリーシート' in header.string:
            return True
        else:
            return False
