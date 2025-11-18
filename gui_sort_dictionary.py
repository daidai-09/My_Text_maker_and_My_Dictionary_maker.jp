import json
import os
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk

# --- 共通設定 (register_data.py より) ---
DATA_FILE = 'dictionary_data.json'
# グローバル変数としてウィジェットを保持
confirm_text = None
# --- GUI デザイン設定 (gui_search_dictionary.py より) ---
FONT_SIZE = 14
BG_COLOR = 'black'
FG_COLOR = 'lime green'
FONT = ('Consolas', FONT_SIZE)

# --- データ操作ロジック (register_data.py より) ---

def load_data():
    """既存のデータをJSONファイルから読み込みます。"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            messagebox.showerror("エラー", f"'{DATA_FILE}'のJSON形式が正しくありません。")
            return []
        except Exception as e:
            messagebox.showerror("エラー", f"ファイルの読み込み中に予期せぬエラーが発生しました: {e}")
            return []
    return []

def save_data(data):
    """データをJSONファイルに保存します。"""
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        messagebox.showerror("エラー", f"ファイルの保存中にエラーが発生しました: {e}")
        return False

def update_confirmation_box(message, tag='normal'):
    """確認ボックスの内容を更新します。(register_data.py より)"""
    global confirm_text
    if confirm_text:
        confirm_text.config(state=tk.NORMAL)
        confirm_text.delete(1.0, tk.END)
        confirm_text.insert(tk.END, message, tag)
        confirm_text.config(state=tk.DISABLED)

# --- 並び替えと保存のロジック ---

def sort_and_save(key_var, reverse_var):
    """選択されたキーと順序に基づいてデータを並び替え、ファイルに保存します。"""
    
    data_list = load_data()
    
    if not data_list:
        update_confirmation_box(f"❌ エラー: データファイル（{DATA_FILE}）に項目が見つかりません。並び替えを中止しました。", 'error')
        return

    # key_var は 'term' に固定されている
    sort_key = key_var.get()
    is_reverse = reverse_var.get() == "降順" # '降順'が選択されたらTrue

    original_count = len(data_list)
    
    try:
        # 並び替えの実行
        sorted_data = sorted(
            data_list, 
            key=lambda item: str(item.get(sort_key, '')).lower(),
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
            confirmation_message += f"  - 並び替えキー: 「{sort_key}」(用語)\n"
            confirmation_message += f"  - 並び替え順序: 「{order_text}」"
            
            update_confirmation_box(confirmation_message, 'success')
            
        else:
            update_confirmation_box("❌ エラー: データファイルの保存に失敗しました。", 'error')

    except Exception as e:
        update_confirmation_box(f"❌ 予期せぬ並び替えエラーが発生しました: {e}", 'error')

# --- GUIのセットアップ (修正部分) ---
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

    # --- 1. 並び替えキーの選択 (固定) ---
    
    tk.Label(main_frame, text="1. 並び替えキー:", **label_style).pack(pady=(10, 2), anchor='w')
    
    # キーを 'term' に固定
    key_var = tk.StringVar(value="term") 
    
    # 【修正箇所】固定キー表示用のスタイルを新しく作成し、**label_styleとのbg重複を回避
    fixed_key_style = label_style.copy()
    # 文字色と背景色を上書きして目立たせる
    fixed_key_style.update({'bg': 'gray15', 'fg': 'yellow'}) 

    tk.Label(main_frame, text=f"キー: {key_var.get()} (用語/単語) - 固定", 
             **fixed_key_style, anchor='w').pack(fill=tk.X, padx=5, pady=5)


    # --- 2. 並び替え順序の選択 ---
    
    tk.Label(main_frame, text="2. 並び替え順序の選択:", **label_style).pack(pady=(10, 2), anchor='w')
    
    order_frame = tk.Frame(main_frame, bg=BG_COLOR)
    order_frame.pack(fill=tk.X)
    
    reverse_var = tk.StringVar(value="昇順") # 初期値は昇順
    
    tk.Radiobutton(order_frame, text="昇順 (A->Z, 0->9)", variable=reverse_var, value="昇順", **radio_style).pack(side=tk.LEFT, padx=(0, 20))
    tk.Radiobutton(order_frame, text="降順 (Z->A, 9->0)", variable=reverse_var, value="降順", **radio_style).pack(side=tk.LEFT)
    
    # --- 3. 実行ボタン ---
    
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
    initial_message = f"データファイル「{DATA_FILE}」を「term」(用語)で並び替え、上書き保存します。\n順序を選択後、ボタンを押してください。"
    update_confirmation_box(initial_message, 'normal')

    root.mainloop()

if __name__ == "__main__":
    setup_gui()