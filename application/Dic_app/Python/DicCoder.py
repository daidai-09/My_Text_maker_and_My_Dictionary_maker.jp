# DicCoder.py
import tkinter as tk
from tkinter import scrolledtext

# constants.py から必要なものをインポート
from constants import (
    DATA_FILE, FONT_SIZE, BG_COLOR, FG_COLOR, FONT, 
    PART_OF_SPEECH_LIST # <--- 追加
)
from data_manager import load_data, save_data

# グローバル変数としてウィジェットを保持
confirm_text = None
entry_term = None
entry_pronunciation = None
entry_definition = None
# entry_part_of_speech を削除し、StringVar に置き換え
part_of_speech_var = None # <--- 新規追加
entry_example = None

def update_confirmation_box(message, tag='normal'):
    """確認ボックスの内容を更新します。"""
    global confirm_text
    if confirm_text:
        confirm_text.config(state=tk.NORMAL)
        confirm_text.delete(1.0, tk.END)
        confirm_text.insert(tk.END, message, tag)
        confirm_text.config(state=tk.DISABLED)

def register_entry_gui():
    """GUIからの入力に基づいて新しい辞書項目を登録します。（重複チェック機能付き）"""
    global entry_term, entry_pronunciation, entry_definition, part_of_speech_var, entry_example # グローバル変数名を修正
    
    key_term = entry_term.get().strip()
    pronunciation = entry_pronunciation.get().strip()
    definition = entry_definition.get().strip()
    # part_of_speech は StringVar から取得
    part_of_speech = part_of_speech_var.get().strip() 
    example = entry_example.get().strip()

    # 1. 入力値チェック (単語/用語は必須)
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
        "pronunciation": pronunciation,
        "definition": definition,
        "part_of_speech": part_of_speech,
        "example": example
    }
    
    data_list.append(new_entry)
    
    if save_data(data_list):
        # 4. 登録内容の確認を出力ボックスに表示
        confirmation_message = "✅ 登録が完了しました。\n"
        confirmation_message += "--- 登録内容の確認 ---\n"
        confirmation_message += f"  - 単語: {key_term}\n"
        confirmation_message += f"  - 発音: {pronunciation}\n"
        confirmation_message += f"  - 意味/定義: {definition}\n"
        confirmation_message += f"  - 品詞: {part_of_speech}\n" # 選択された品詞
        confirmation_message += f"  - 使用例: {example}\n"
        
        update_confirmation_box(confirmation_message, 'success')
        
        # 5. 登録後、入力フィールドをクリア
        entry_term.delete(0, tk.END)
        entry_pronunciation.delete(0, tk.END)
        entry_definition.delete(0, tk.END)
        # 品詞はOptionMenuなので、クリアせず最初の項目に戻す
        if PART_OF_SPEECH_LIST:
            part_of_speech_var.set(PART_OF_SPEECH_LIST[0])
        entry_example.delete(0, tk.END)
    else:
        update_confirmation_box("❌ エラー: データファイルの保存に失敗しました。", 'error')


# --- GUIのセットアップ ---
def setup_gui():
    global entry_term, entry_pronunciation, entry_definition, part_of_speech_var, entry_example, confirm_text # グローバル変数名を修正
    
    root = tk.Tk()
    root.title("DicCoder V1.2")
    
    root.configure(bg=BG_COLOR)

    # ウィジェットのスタイル設定
    label_style = {'bg': BG_COLOR, 'fg': FG_COLOR, 'font': FONT}
    entry_style = {'bg': 'gray15', 'fg': FG_COLOR, 'insertbackground': FG_COLOR, 'font': FONT, 'relief': tk.SOLID, 'bd': 1}
    button_style = {'bg': 'darkgreen', 'fg': FG_COLOR, 'font': (FONT[0], FONT_SIZE, 'bold'), 'activebackground': 'green', 'activeforeground': 'white', 'relief': tk.RAISED, 'bd': 2}
    text_area_style = {'bg': 'gray15', 'fg': FG_COLOR, 'font': ('Consolas', 12), 'relief': tk.SUNKEN, 'bd': 2, 'insertbackground': FG_COLOR}
    
    # OptionMenu 用のスタイル設定 (幅を調整)
    option_menu_style = {
        'bg': 'gray15', 'fg': FG_COLOR, 'font': FONT,
        'activebackground': 'darkgreen', 'activeforeground': 'white',    
        'relief': tk.SOLID, 'bd': 1, 'width': 5 
    }
    
    # メインフレーム
    main_frame = tk.Frame(root, bg=BG_COLOR, padx=20, pady=10)
    main_frame.pack(expand=True, fill=tk.BOTH)

    # --- 入力フィールドの配置 ---
    
    # 1. 単語
    tk.Label(main_frame, text="1. 単語 (検索キー):", **label_style).pack(pady=(10, 2), anchor='w')
    entry_term = tk.Entry(main_frame, width=50, **entry_style)
    entry_term.pack(fill=tk.X)
    
    # 2. 発音
    tk.Label(main_frame, text="2. 発音:", **label_style).pack(pady=(10, 2), anchor='w')
    entry_pronunciation = tk.Entry(main_frame, width=50, **entry_style)
    entry_pronunciation.pack(fill=tk.X)
    
    # 3. 意味・定義
    tk.Label(main_frame, text="3. 意味・定義:", **label_style).pack(pady=(10, 2), anchor='w')
    entry_definition = tk.Entry(main_frame, width=50, **entry_style)
    entry_definition.pack(fill=tk.X)
    
    # 4. 品詞 (OptionMenuに変更)
    tk.Label(main_frame, text="4. 品詞:", **label_style).pack(pady=(10, 2), anchor='w')
    
    part_of_speech_var = tk.StringVar(root)
    # 初期値をリストの最初の項目に設定
    if PART_OF_SPEECH_LIST:
        part_of_speech_var.set(PART_OF_SPEECH_LIST[0]) 

    option_menu = tk.OptionMenu(main_frame, part_of_speech_var, *PART_OF_SPEECH_LIST)
    option_menu.config(**option_menu_style)
    
    # ドロップダウンメニューの内部の見た目を設定
    menu = root.nametowidget(option_menu.menuname)
    menu.config(
        bg='gray15', fg='lime green', font=FONT,
        activebackground='darkgreen', activeforeground='white'
    )
    
    option_menu.pack(fill=tk.X) # OptionMenuを配置
    
    # 5. 使用例
    tk.Label(main_frame, text="5. 使用例:", **label_style).pack(pady=(10, 2), anchor='w')
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