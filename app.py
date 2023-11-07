import streamlit as st
from applications.scraper_app import app as onecareer_app
from applications.embedding_app import app as embedding_app
from applications.generator_app import app as rag_app


# Define the multipage class to manage the multiple apps in our program
class MultiPage:
    def __init__(self) -> None:
        self.pages = []

    def add_page(self, title, func) -> None:
        self.pages.append({
                "title": title,
                "function": func
            })

    def run(self):
        st.sidebar.title('Navigation')
        # ここでページオブジェクトを選択させている
        page = st.sidebar.radio('Go to', self.pages, format_func=lambda page: page['title'])
        # 取得したページオブジェクトを実行することでページを表示する
        page['function']()


# Create an instance of the app
app = MultiPage()

# Add all your applications (pages) here
app.add_page("Generator", rag_app)
app.add_page("Scraper", onecareer_app)
app.add_page("Embedding", embedding_app)

# The main app
app.run()
