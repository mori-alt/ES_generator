# スクレイピングした情報をもとにESを作成  
## スクレイピングの方法  
- app.pyをstreamlitで起動
- アカウント情報の入力
- 取得したい企業のES一覧ページを入力（デフォルトでは指定無しで最新版から順に取得）
- start scraping
- ESの生データの取得

## スクレイピングしたデータの加工
- ./process_data/embedding_app.pyをstreamlitで起動
- 取得した企業情報の入力
- make .txt
- embedding
- 取得したES生データの埋め込み

## ES生成の方法
- rag.pyをstreamlitで起動
- 対象とする企業名の入力（ディレクトリ名と一致させる）
- 企業情報について補足を入力
- 自分の情報の入力
- Generate
- ES完成
