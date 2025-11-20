# gui_sort_dictionary.py
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk

from constants import DATA_FILE, FONT_SIZE, BG_COLOR, FG_COLOR, FONT, DICTIONARY_FIELDS
from data_manager import load_data, save_data

# グローバル変数としてウィジェットを保持
confirm_text = None

def update_confirmation_box(message, tag='normal'):
    """確認ボックスの内容を更新します。"""
    global confirm_text
    if confirm_text:
        confirm_text.config(state=tk.NORMAL)
        confirm_text.delete(1.0, tk.END)
        confirm_text.insert(tk.END, message, tag)
        confirm_text.config(state=tk.DISABLED)

# --- 並び替えと保存のロジック ---

# key_varはComboboxのStringVar、reverse_varはRadiobuttonのStringVar
def sort_and_save(key_var, reverse_var):
    """選択されたキーと順序に基づいてデータを並び替え、ファイルに保存します。"""
    
    data_list = load_data()
    
    if not data_list:
        update_confirmation_box(f"❌ エラー: データファイル（{DATA_FILE}）に項目が見つかりません。並び替えを中止しました。", 'error')
        return

    # 選択されたキーと順序を取得
    sort_key = key_var.get()
    is_reverse = reverse_var.get() == "降順" # '降順'が選択されたらTrue

    # 表示名から実際のキー名 (例: '単語 (term)' -> 'term') を抽出
    # DICTIONARY_FIELDS のキーと値が逆になった辞書を作成して検索
    display_to_key = {v: k for k, v in DICTIONARY_FIELDS.items()}
    actual_sort_key = display_to_key.get(sort_key, 'term') # 安全策として見つからなければ 'term'

    original_count = len(data_list)
    
    try:
        # 並び替えの実行 (大文字小文字を区別しないソート)
        sorted_data = sorted(
            data_list, 
            key=lambda item: str(item.get(actual_sort_key, '')).lower(),
            reverse=is_reverse
        )
        
        # ファイルへ保存
        if save_data(sorted_data):
            
            # 確認メッセージを作成
            order_text = "降順 (Z->A, 9->0)" if is_reverse else "昇順 (A->Z, 0->9)"
            
            confirmation_message = "✅ 並び替えと保存が完了しました。\n"
            confirmation_message += "--- 実行内容 ---\n"
            confirmation_message += f"  - 対象ファイル: {DATA_FILE}\n"
            confirmation_message += f"  - 処理された項目数: {original_count}件\n"
            confirmation_message += f"  - 並び替えキー: 「{sort_key}」（内部キー: {actual_sort_key}）\n"
            confirmation_message += f"  - 並び替え順序: 「{order_text}」"
            
            update_confirmation_box(confirmation_message, 'success')
            
        else:
            update_confirmation_box("❌ エラー: データファイルの保存に失敗しました。", 'error')

    except Exception as e:
        update_confirmation_box(f"❌ 予期せぬ並び替えエラーが発生しました: {e}", 'error')

# --- GUIのセットアップ ---
def setup_gui():
    global confirm_text
    
    root = tk.Tk()
    root.title("辞書項目並び替え・保存アプリケーション")
    
    root.configure(bg=BG_COLOR)

    # ttkスタイル設定（Comboboxのデザイン調整）
    style = ttk.Style()
    style.theme_use('clam')
    style.configure("TCombobox", fieldbackground='gray15', background='gray15', foreground='lime green', 
                    selectbackground='darkgreen', selectforeground='white', font=FONT)
    style.map("TCombobox", fieldbackground=[('readonly', 'gray15')], background=[('active', 'darkgreen')])

    # ウィジェットのスタイル設定
    label_style = {'bg': BG_COLOR, 'fg': FG_COLOR, 'font': FONT}
    button_style = {'bg': 'darkgreen', 'fg': FG_COLOR, 'font': (FONT[0], FONT_SIZE, 'bold'), 'activebackground': 'green', 'activeforeground': 'white', 'relief': tk.RAISED, 'bd': 2}
    text_area_style = {'bg': 'gray15', 'fg': FG_COLOR, 'font': ('Consolas', 12), 'relief': tk.SUNKEN, 'bd': 2, 'insertbackground': FG_COLOR}
    radio_style = {'bg': BG_COLOR, 'fg': FG_COLOR, 'font': FONT, 'selectcolor': 'gray15'}

    # メインフレーム
    main_frame = tk.Frame(root, bg=BG_COLOR, padx=20, pady=10)
    main_frame.pack(expand=True, fill=tk.BOTH)

    # --- 1. 並び替えキーの選択 ---
    tk.Label(main_frame, text="並び替えキーの選択:", **label_style).pack(pady=(10, 2), anchor='w')

    key_var = tk.StringVar()
    sort_keys_display = list(DICTIONARY_FIELDS.values())
    
    sort_key_combo = ttk.Combobox(main_frame, textvariable=key_var, values=sort_keys_display, state='readonly', font=FONT)
    sort_key_combo.set(DICTIONARY_FIELDS['term']) # 初期値は '単語 (term)'
    sort_key_combo.pack(fill=tk.X)
    
    # --- 2. 並び替え順序の選択 ---
    
    tk.Label(main_frame, text="並び替え順序の選択:", **label_style).pack(pady=(10, 2), anchor='w')
    
    order_frame = tk.Frame(main_frame, bg=BG_COLOR)
    order_frame.pack(fill=tk.X)
    
    reverse_var = tk.StringVar(value="昇順") # 初期値は昇順
    
    tk.Radiobutton(order_frame, text="昇順 (A->Z, 0->9)", variable=reverse_var, value="昇順", **radio_style).pack(side=tk.LEFT, padx=(0, 20))
    tk.Radiobutton(order_frame, text="降順 (Z->A, 9->0)", variable=reverse_var, value="降順", **radio_style).pack(side=tk.LEFT)
    
    # --- 3. 実行ボタン (修正済) ---
    
    register_button = tk.Button(main_frame, text=f"📂 {DATA_FILE} を並び替えて上書き保存", 
                                command=lambda: sort_and_save(key_var, reverse_var), **button_style)
    register_button.pack(pady=20, fill=tk.X)

    # --- 4. 確認ボックス ---
    tk.Label(main_frame, text="--- 実行確認 / メッセージ ---", **label_style).pack(pady=(10, 0), anchor='w')
    
    confirm_text = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, height=6, **text_area_style, state=tk.DISABLED)
    confirm_text.pack(pady=10, fill=tk.X)
    
    # テキストの色付け設定
    confirm_text.tag_config('error', foreground='red')
    confirm_text.tag_config('warning', foreground='yellow')
    confirm_text.tag_config('success', foreground=FG_COLOR, font=(FONT[0], FONT_SIZE, 'bold'))

    # 初期メッセージ
    initial_message = f"データファイル「{DATA_FILE}」を上書き保存します。\nキーと順序を選択後、ボタンを押してください。"
    update_confirmation_box(initial_message, 'normal')

    root.mainloop()

if __name__ == "__main__":
    setup_gui()