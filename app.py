from scrapers.OneCareerScraper import OneCareerScraper
import streamlit as st
import os


def user_info_form():
    default_username = os.environ.get('ONECAREER_USERNAME')
    default_password = os.environ.get('ONECAREER_PASSWORD')
    default_start_url = 'https://www.onecareer.jp/experiences?company=&commit=%E7%B5%9E%E3%82%8A%E8%BE%BC%E3%82%80&business_category_id=&business_subcategory_id='

    url_input = st.text_input("URLを入力して下さい", value=default_start_url)
    username_input = st.text_input("ユーザ名を入力してください", value=default_username)
    pwd_input = st.text_input("パスワードを入力してください", type='password', value=default_password)

    st.write("あなたが入力したURLは：", url_input)
    st.write("あなたが入力したユーザ名は：", username_input)

    return url_input, username_input, pwd_input


def main():
    st.title("Onecareer Scraping")

    login_url = 'https://www.onecareer.jp/users/sign_in'
    url_input, username_input, pwd_input = user_info_form()
    credentials = {'username': username_input, 'password': pwd_input}

    if st.button('start scraping'):
        scraper = OneCareerScraper(login_url, url_input, credentials)
        scraper.crawl(url_input)


if __name__ == "__main__":
    main()
