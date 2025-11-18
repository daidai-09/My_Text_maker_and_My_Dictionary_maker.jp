import json
import os
import tkinter as tk
from tkinter import scrolledtext

DATA_FILE = 'dictionary_data.json'

# グローバル変数としてウィジェットを保持
confirm_text = None

def load_data():
    """既存のデータをJSONファイルから読み込みます。"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_data(data):
    """データをJSONファイルに保存します。"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def update_confirmation_box(message, tag='normal'):
    """確認ボックスの内容を更新します。"""
    confirm_text.config(state=tk.NORMAL)
    confirm_text.delete(1.0, tk.END)
    confirm_text.insert(tk.END, message, tag)
    confirm_text.config(state=tk.DISABLED)

def register_entry_gui():
    """GUIからの入力に基づいて新しい辞書項目を登録します。（重複チェック機能付き）"""
    
    key_term = entry_term.get().strip()
    definition = entry_definition.get().strip()
    category = entry_category.get().strip()
    example = entry_example.get().strip()

    # 1. 入力値チェック
    if not key_term:
        update_confirmation_box("❌ エラー: 検索キーとなる用語/単語は必須です。", 'error')
        return

    data_list = load_data()

    # 2. 重複チェック
    for entry in data_list:
        if entry.get('term') == key_term:
            update_confirmation_box(f"⚠️ 警告: この用語（{key_term}）は既に登録されています。\n登録を中止しました。", 'warning')
            return

    # 3. 新しいエントリーを作成・保存
    new_entry = {
        "term": key_term,
        "definition": definition,
        "category": category,
        "example": example
    }
    
    data_list.append(new_entry)
    save_data(data_list)
    
    # 4. 登録内容の確認を出力ボックスに表示
    confirmation_message = "✅ 登録が完了しました。\n"
    confirmation_message += "--- 登録内容の確認 ---\n"
    confirmation_message += f"  - 用語: {key_term}\n"
    confirmation_message += f"  - 定義: {definition}\n"
    confirmation_message += f"  - カテゴリ: {category}\n"
    confirmation_message += f"  - 使用例: {example}\n"
    
    update_confirmation_box(confirmation_message, 'success')
    
    # 5. 登録後、入力フィールドをクリア
    entry_term.delete(0, tk.END)
    entry_definition.delete(0, tk.END)
    entry_category.delete(0, tk.END)
    entry_example.delete(0, tk.END)

# --- GUIのセットアップ ---
def setup_gui():
    global entry_term, entry_definition, entry_category, entry_example, confirm_text
    
    root = tk.Tk()
    root.title("辞書項目登録アプリケーション")
    
    # フォントサイズの設定
    FONT_SIZE = 14
    
    # デザイン設定
    BG_COLOR = 'black'
    FG_COLOR = 'lime green'
    FONT = ('Consolas', FONT_SIZE)
    
    root.configure(bg=BG_COLOR)

    # ウィジェットのスタイル設定
    label_style = {'bg': BG_COLOR, 'fg': FG_COLOR, 'font': FONT}
    entry_style = {'bg': 'gray15', 'fg': FG_COLOR, 'insertbackground': FG_COLOR, 'font': FONT, 'relief': tk.SOLID, 'bd': 1}
    button_style = {'bg': 'darkgreen', 'fg': FG_COLOR, 'font': ('Consolas', FONT_SIZE, 'bold'), 'activebackground': 'green', 'activeforeground': 'white', 'relief': tk.RAISED, 'bd': 2}
    text_area_style = {'bg': 'gray15', 'fg': FG_COLOR, 'font': ('Consolas', 12), 'relief': tk.SUNKEN, 'bd': 2, 'insertbackground': FG_COLOR} # 確認ボックスは少し小さめのフォント
    
    # メインフレーム
    main_frame = tk.Frame(root, bg=BG_COLOR, padx=20, pady=10)
    main_frame.pack(expand=True, fill=tk.BOTH)

    # --- 入力フィールドの配置 (変更なし) ---
    
    tk.Label(main_frame, text="1. 検索キーとなる用語/単語:", **label_style).pack(pady=(10, 2), anchor='w')
    entry_term = tk.Entry(main_frame, width=50, **entry_style)
    entry_term.pack(fill=tk.X)
    
    tk.Label(main_frame, text="2. 定義/主要な説明:", **label_style).pack(pady=(10, 2), anchor='w')
    entry_definition = tk.Entry(main_frame, width=50, **entry_style)
    entry_definition.pack(fill=tk.X)
    
    tk.Label(main_frame, text="3. カテゴリ/分野:", **label_style).pack(pady=(10, 2), anchor='w')
    entry_category = tk.Entry(main_frame, width=50, **entry_style)
    entry_category.pack(fill=tk.X)
    
    tk.Label(main_frame, text="4. 使用例/補足説明:", **label_style).pack(pady=(10, 2), anchor='w')
    entry_example = tk.Entry(main_frame, width=50, **entry_style)
    entry_example.pack(fill=tk.X)
    
    # 登録ボタン
    register_button = tk.Button(main_frame, text="✅ 項目を登録", command=register_entry_gui, **button_style)
    register_button.pack(pady=20, fill=tk.X)

    # --- 確認ボックスの追加 ---
    tk.Label(main_frame, text="--- 登録確認 / メッセージ ---", **label_style).pack(pady=(10, 0), anchor='w')
    
    confirm_text = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, height=6, **text_area_style, state=tk.DISABLED)
    confirm_text.pack(pady=10, fill=tk.X)
    
    # テキストの色付け設定
    confirm_text.tag_config('error', foreground='red')
    confirm_text.tag_config('warning', foreground='yellow')
    confirm_text.tag_config('success', foreground=FG_COLOR, font=(FONT[0], FONT_SIZE, 'bold'))

    # 初期メッセージ
    update_confirmation_box("入力後、「項目を登録」ボタンを押してください。", 'normal')

    root.mainloop()

if __name__ == "__main__":
    setup_gui()