# パッケージのインポート
import json
import os
import streamlit as st
import openai

from dotenv import load_dotenv
from llama_index import StorageContext, load_index_from_storage


def app():
    # 環境変数の設定
    load_dotenv()
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

    # apiに投げるためのプロンプトの読み込み
    # load functions from json file
    # ファンクションコーリング用のjsonファイル
    if 'functions' not in st.session_state:
        try:
            with open('./res/prompts/functions.json', 'r', encoding='utf-8') as f:
                st.session_state.functions = json.load(f)
        except FileNotFoundError:
            st.error("Couldn't load functions!")
            st.session_state.functions = []

    # load prompts from json file
    # 動作とふるまいを求めるためのjsonファイル
    if 'prompts' not in st.session_state:
        try:
            with open('./res/prompts/prompts.json', 'r', encoding='utf-8') as f:
                st.session_state.prompts = json.load(f)
        except FileNotFoundError:
            st.error("Couldn't load prompts!")
            st.session_state.prompts = []


    st.title("ES Maker")

    company_name = st.text_input("応募したい会社名を教えてね。", "ファーストリテイリング")
    position = st.text_input("応募したいポジションを教えてね。", "エンジニア")
    classification = st.radio("文系か理系か教えてね。", ("LiberalArts", "Sciences"))

    # 読み込みするディレクトリの作成
    input_path = f"./res/embedding/{company_name}/{classification}"
    if not os.path.exists(input_path):
        st.warning("この企業に関するデータはまだありません。別の企業の選択をするか、scraping、embeddingの処理をしてください。")

    company_features = st.text_input("応募したい会社の特色を教えてね。", "グローバルに展開している・最先端技術を駆使している・一つの事業に特化している")
    company_keywords = st.text_input("応募したい会社のキーワードを教えてね。", "・大義名分・常に改善、常に前進・品性高潔・信念不抜")
    appeal_points = st.text_input("あなたのアピールしたいポイントをカンマ区切りで教えてね。", "プログラミングスキル、コミュニケーション能力、問題解決能力、チームワーク")
    self_promotion = st.text_area("自己PRを教えてね。", "私の強みは、常に新しいことに挑戦し続け、目標達成に向かい決して諦めずに努力を継続できることです。研究を通じて機械学習や並列計算の知識を深め、最適化問題の効率的な収束や、処理時間を350倍以上高速化することに成功しました。研究が行き詰まっても、諦めず成果を出すまで努力を続ける力を養うことが出来ました。また、世界各国から集まったMLエンジニア達のもとで、完全英語環境下で1ヶ月半に渡り就業型インターンを経験し、LLMやAIを活用した業務を経験しました。このような実践的な経験を通して、現状の問題点を分析して解決する能力や、LLM、AIに関する最先端の知識とスキルを専門レベルで磨くことができました。私が持つ技術力だけでなく、多言語、文化の環境での会話能力も併せ持つ、国際的な視野で活躍できるエンジニアであると自負しております。今後は、更なる技術革新に貢献し、業界全体を牽引する存在になることが目標です。")
    # テキストの分割
    lines = appeal_points.split("、")
    # ノードの準備
    nodes = []
    adjusted_text_list = []

    # streamするか
    stream = True

    # ログ出力のパス作成
    log_path = f"./res/logs/{company_name}/{classification}/nodes.json"

    # 使うPromptの選択
    # 指示とかふるまいとかを定義している role: system
    st.session_state.selected_prompt_name = st.selectbox("Select the prompt", [prompt_name['name'] for prompt_name in st.session_state.prompts])
    st.session_state.selected_prompt = next((prompt['prompt'] for prompt in st.session_state.prompts if prompt['name'] == st.session_state.selected_prompt_name), None)
    # 使うFunctionの選択
    # 具体的な作業内容の指示 role: user
    st.session_state.function_name = st.selectbox("Select the function", [function['name'] for function in st.session_state.functions])

    # 何個のノードを返すか
    st.sidebar.markdown("---")
    num_nodes = st.sidebar.slider("Number of nodes", 1, 10, 3)
    # 使うモデルの選択
    model = st.sidebar.selectbox("Select the model", ["gpt-3.5-turbo-0613", "gpt-4-0613", "gpt-3.5-turbo-16k-0613"])
    # どれくらいクリエイティブにするか
    temperature = st.sidebar.slider("temperature", 0.0, 1.0, 0.8)

    if st.button("Generate"):
        print("clicked generate button")
        st.write(f"read data from {input_path}")
        # vector dataの読み込み
        print("load vector data")
        if 'vector_data' not in st.session_state:
            with st.spinner("Loading Vector Data ..."):
                st.session_state.vector_data = StorageContext.from_defaults(persist_dir=input_path)

        # インデックスの読み込み
        print("load index")
        index = load_index_from_storage(st.session_state.vector_data)

        # Retriever の作成
        print("create retriever")
        retriever = index.as_retriever(similarity_top_k=num_nodes)

        # ログ出力用ディレクトリの作成
        print("make log dir")
        if not os.path.exists(os.path.dirname(log_path)):
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            print(f"make dir: {os.path.dirname(log_path)}")

        # 生成
        print("generate")
        with st.spinner("Generating ..."):
            print("start generating")
            for i, line in enumerate(lines):
                retrieval_result = retriever.retrieve(line)
                nodes_entry = {"target": line, "nodes": []}
                for node in retrieval_result:
                    nodes_entry["nodes"].append({"score": node.score, "text": node.text})
                nodes.append(nodes_entry)

            # todo 書き込むファイルの方には全てのノードのスコアを書き込んで後で評価したい
            print("write log")
            with open(log_path, "w", encoding="utf-8") as f:
                json.dump(nodes, f, indent=4, ensure_ascii=False)

            print("adjust text")
            for node in nodes:
                for sub_node in node['nodes']:
                    text = sub_node['text']
                    if text.startswith('。'):
                        adjusted_text = text[1:] + '。'
                        adjusted_text_list.append(adjusted_text)
                    else:
                        adjusted_text_list.append(text)

            combined_text = ' '.join(adjusted_text_list)

            print(f"combined_text: {combined_text}")
            st.info(combined_text)

            input_query = f"CompanyName: [{company_name}]\n　Position: [{position}]\n CompanyFeatures: [{company_features}]\n CompanyKeywords: [{company_keywords}]\n Entry sheet fragments of others who applied to the same company: [{combined_text}]\n MY Appeal Points: [{appeal_points}]\n MY PR Statement: [{self_promotion}]\n"
            print(f"input_query: {input_query}")
            # st.info(input_query)

            # create response
            completion = openai.ChatCompletion.create(
                model=model,
                messages=[
                    {"role": "system", "content": st.session_state.selected_prompt},
                    {"role": "user", "content": input_query}
                ],
                temperature=temperature,
                functions=st.session_state.functions,
                function_call={"name": st.session_state.function_name},
                stream=stream,
            )
            print('completion: ', completion)
            print('type: ', type(completion))

            if stream:
                result_area = st.empty()
                texts = ''
                for chunk in completion:
                    if "function_call" in chunk.choices[0].delta:
                        text = chunk['choices'][0]['delta']['function_call']['arguments']
                        texts += text
                        result_area.write(texts)

            else:
                # todo ストリームにしないとここでたまにjson破損のエラーがでるから出ないように修正したい
                st.warning(completion.usage)  # tokenの利用数を表示
                st.warning(f"estimated total fee: {completion.usage['total_tokens'] * 0.000002 * 150} yen  (1USD = 150 yen)")
                print(completion.choices[0].message.to_dict()['function_call']['arguments'])
                print(json.loads(completion.choices[0].message.to_dict()['function_call']['arguments']))
                st.success(json.loads(completion.choices[0].message.to_dict()['function_call']['arguments']))


if __name__ == "__main__":
    app()
