# constants.py

# --- ファイル設定 ---
DATA_FILE = 'dictionary_data.json'

# --- GUI デザイン設定 ---
FONT_SIZE = 14
BG_COLOR = 'black'
FG_COLOR = 'lime green'
FONT = ('Consolas', FONT_SIZE)

# --- 辞書フィールドの定義 ---
# 並び替えや検索で利用可能なキーと、GUI表示名のマッピング
DICTIONARY_FIELDS = {
    "term": "単語 (term)",
    "pronunciation": "発音 (pronunciation)",
    "definition": "意味・定義 (definition)",
    "part_of_speech": "品詞 (part_of_speech)",
    "example": "使用例 (example)"
}

# --- 品詞の定義 (新規追加) ---
PART_OF_SPEECH_LIST = [
    "N(名詞)", "V(動詞)", "Adj(形容詞)", "Adv(副詞)", "Conj(接続詞)", 
    "Prep(前置詞)", "Pro(代名詞)", "Det(限定詞)", "Aux(助動詞)", "Part(助詞)","Num(数詞)",
    # 必要に応じてカスタム品詞を追加してください
]