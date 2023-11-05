import os
import json
import time
import streamlit as st
from embedding import embedding


def get_files_excluding_specific_directory(directory_path, exclude_directory_name):
    all_files = []
    for root, dirs, files in os.walk(directory_path):
        # exclude_directory_nameをdirsから除外することで、そのディレクトリは走査されない
        if exclude_directory_name in dirs:
            dirs.remove(exclude_directory_name)

        # ファイルをリストに追加
        for file in files:
            full_path = os.path.join(root, file)
            all_files.append(full_path)

    return all_files


def app():
    if "make_txt_clicked" not in st.session_state:
        st.session_state.make_txt_clicked = False

    if "make_txt_completed" not in st.session_state:
        st.session_state.make_txt_completed = False

    st.title("Make .txt for embedding")
    st.write(os.getcwd())
    # ディレクトリの指定
    base_dir = "./res/ES_scraping"
    subdirs = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]

    # ユーザーからの入力を受け取る
    user_input = st.text_input("Search for a directory:", value="ファーストリテイリング")

    # 入力を基にフィルタリングして表示
    filtered_subdirs = [d for d in subdirs if user_input.lower() in d.lower()]

    if filtered_subdirs:
        # フィルタリングされたディレクトリの一覧を表示
        selected_subdir = st.selectbox("Select a directory:", filtered_subdirs)
        st.write(f"Selected: {selected_subdir}")

        # 文理選択
        classification = st.radio("Classification", ("LiberalArts", "Sciences"))
        st.write(f"Selected classification: {classification}")

        if classification in os.listdir(os.path.join(base_dir, selected_subdir)):
            file_path = os.path.join(base_dir, selected_subdir, classification)
            json_files = get_files_excluding_specific_directory(file_path, "nothings")

            qa_pairs = []
            if st.button("make .txt"):
                for json_file in json_files:
                    with open(json_file, "r", encoding="utf-8") as f:
                        json_data = json.load(f)
                        for qa_pair in json_data["qa_pairs"]:
                            qa_pairs.append("-" + qa_pair["question"])
                            qa_pairs.append("-" + qa_pair["answer"])

                output_dir_path = os.path.join("./res/for_embedding", selected_subdir, classification)
                os.makedirs(output_dir_path, exist_ok=True)
                print(f"output_dir_path: {output_dir_path}")
                with open(output_dir_path + "/output.txt", "w", encoding="utf-8") as f:
                    f.write("\n".join(qa_pairs))
                st.session_state.make_txt_clicked = True

            if st.session_state.make_txt_clicked:
                st.write(f"Output data: {selected_subdir}  {classification}")
                st.write(f"file num : {len(json_files)}")
                st.write(f"output lines num : {len(qa_pairs)}")
                st.success("File has been written successfully!")
                st.session_state.make_txt_completed = True

            if st.session_state.make_txt_completed:
                if st.button("embedding"):
                    with st.spinner("embedding ..."):
                        input_for_embedding_path = os.path.join("./res/for_embedding", selected_subdir, classification)
                        output_embedding_path = os.path.join("./res/embedding", selected_subdir, classification)

                        print(f"input_for_embedding_path: {input_for_embedding_path}")
                        print(f"output_embedding_path: {output_embedding_path}")

                        embedding(input_dir=input_for_embedding_path, output_dir=output_embedding_path)

                    print("finished embedding!")
                    st.success("embedding completed!")

        else:
            st.warning("No classification match your search. Please try a different name.")

    else:
        # フィルタリングにかからなければ警告を表示
        st.warning("No directories match your search. Please try a different name.")


if __name__ == "__main__":
    # 実行時は streamlit run ./process_data/embedding_app.py
    app()
