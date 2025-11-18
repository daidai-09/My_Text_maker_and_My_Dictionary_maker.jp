import json
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

# --- データの読み込みと検索ロジック ---

# グローバル変数として読み込んだ全データを保持
loaded_data = []

# ウィジェットをグローバルで保持
result_text = None
search_entry = None
search_scope_combo = None

def load_data_from_file():
    """ファイル選択ダイアログを表示し、JSONファイルを読み込み、全データを表示エリアに流し込みます。"""
    global loaded_data
    
    filepath = filedialog.askopenfilename(
        defaultextension=".json",
        filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        title="辞書データファイルを選択してください"
    )
    
    if not filepath:
        return

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        
        messagebox.showinfo("読み込み完了", f"データが正常に読み込まれました。\n項目数: {len(loaded_data)}件")
        
        # 読み込み後、全データを結果表示エリアに出力
        search_and_display()
        
    except FileNotFoundError:
        messagebox.showerror("エラー", "ファイルが見つかりません。")
        loaded_data = []
        display_results([])
    except json.JSONDecodeError:
        messagebox.showerror("エラー", "JSONファイルの形式が正しくありません。")
        loaded_data = []
        display_results([])
    except Exception as e:
        messagebox.showerror("エラー", f"予期せぬエラーが発生しました: {e}")
        loaded_data = []
        display_results([])

def search_and_display(event=None):
    """検索ボックスの入力と検索ジャンルに基づいてデータをフィルタリングし、結果を表示します。"""
    
    if not loaded_data:
        display_results([])
        return
        
    search_term = search_entry.get().lower().strip()
    selected_scope = search_scope_combo.get()
    
    # 検索ジャンルとデータキーのマッピング
    scope_map = {
        "全項目": ["term", "definition", "category", "example"],
        "用語 (term)": ["term"],
        "意味/定義 (definition)": ["definition"],
        "カテゴリ/分野 (category)": ["category"]
    }
    
    search_keys = scope_map.get(selected_scope, scope_map["全項目"])
    
    # 検索キーワードがない場合は、全データを表示
    if not search_term:
        display_results(loaded_data)
        return
    
    results = []
    
    # フィルタリング検索
    for entry in loaded_data:
        found = False
        # 選択された検索キーのみをチェック
        for key in search_keys:
            if search_term in entry.get(key, '').lower():
                results.append(entry)
                found = True
                break
            
    display_results(results, search_term)


def display_results(results, search_term=""):
    """指定されたデータを結果表示エリアに整形して出力します。"""
    result_text.config(state=tk.NORMAL)
    result_text.delete(1.0, tk.END)
    
    if not loaded_data and not results:
        result_text.insert(tk.END, "データを読み込んでください。", 'info')
    elif not results and search_term:
        result_text.insert(tk.END, f"キーワード「{search_term}」に一致する項目は見つかりませんでした。", 'info')
    elif not results and not search_term:
         result_text.insert(tk.END, "データが読み込まれていません。", 'info')
    else:
        # ヘッダー表示
        header_text = f"--- 表示項目数: {len(results)}件 (全{len(loaded_data)}件中) ---\n\n"
        
        result_text.insert(tk.END, header_text, 'header')
        
        # 各項目の整形出力
        for i, result in enumerate(results, 1):
            result_text.insert(tk.END, f"[{i}] 用語: {result.get('term', 'N/A')}\n", 'term')
            result_text.insert(tk.END, f"  定義: {result.get('definition', 'N/A')}\n")
            result_text.insert(tk.END, f"  カテゴリ: {result.get('category', 'N/A')}\n")
            result_text.insert(tk.END, f"  使用例: {result.get('example', 'N/A')}\n\n")

    result_text.config(state=tk.DISABLED)

# --- GUIの構築とデザイン設定 ---

def setup_gui():
    global search_entry, result_text, search_scope_combo
    
    root = tk.Tk()
    root.title("辞書検索アプリケーション")
    
    # --- デザイン設定 ---
    FONT_SIZE = 14 # フォントサイズを14に設定
    BG_COLOR = 'black'
    FG_COLOR = 'lime green'
    FONT = ('Consolas', FONT_SIZE)
    
    root.configure(bg=BG_COLOR)
    
    # Tkinterのttkスタイルを設定 (Comboboxのデザインを調整するため)
    style = ttk.Style()
    style.theme_use('clam')
    
    # TComboboxのフォントを新しいサイズに設定
    style.configure("TCombobox", fieldbackground='gray15', background='gray15', foreground='lime green', 
                    selectbackground='darkgreen', selectforeground='white', font=FONT)
    style.map("TCombobox", fieldbackground=[('readonly', 'gray15')], background=[('active', 'darkgreen')])

    # ウィジェットの共通スタイル設定
    label_style = {'bg': BG_COLOR, 'fg': FG_COLOR, 'font': FONT}
    entry_style = {'bg': 'gray15', 'fg': FG_COLOR, 'insertbackground': FG_COLOR, 'font': FONT, 'relief': tk.SOLID, 'bd': 1}
    button_style = {'bg': 'darkgreen', 'fg': FG_COLOR, 'font': FONT, 'activebackground': 'green', 'activeforeground': 'white', 'relief': tk.RAISED, 'bd': 2}
    text_area_style = {'bg': 'gray15', 'fg': FG_COLOR, 'font': FONT, 'relief': tk.SUNKEN, 'bd': 2, 'insertbackground': FG_COLOR}
    
    main_frame = tk.Frame(root, bg=BG_COLOR, padx=10, pady=10)
    main_frame.pack(expand=True, fill=tk.BOTH)

    # 1. データ読み込みボタン
    load_button = tk.Button(main_frame, text="📂 データ読み込み", command=load_data_from_file, **button_style)
    load_button.pack(pady=(0, 10), fill=tk.X)

    # 2. 検索コントロールフレーム (ComboboxとEntryを配置)
    control_frame = tk.Frame(main_frame, bg=BG_COLOR)
    control_frame.pack(pady=5, fill=tk.X)
    
    tk.Label(control_frame, text="🔍 検索ジャンル:", **label_style).pack(side=tk.LEFT, padx=(0, 5))

    # --- 検索ジャンル Combobox ---
    search_scopes = ["全項目", "用語 (term)", "意味/定義 (definition)", "カテゴリ/分野 (category)"]
    search_scope_combo = ttk.Combobox(control_frame, values=search_scopes, state='readonly', width=20, font=FONT)
    search_scope_combo.set(search_scopes[0])
    search_scope_combo.pack(side=tk.LEFT, padx=(0, 10))
    search_scope_combo.bind("<<ComboboxSelected>>", search_and_display)

    # 検索入力ボックス
    search_entry = tk.Entry(control_frame, width=30, **entry_style)
    search_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)
    search_entry.bind('<KeyRelease>', search_and_display)

    # 3. 検索結果表示エリア
    tk.Label(main_frame, text="--- データ一覧 / 検索結果 ---", **label_style).pack(pady=(10, 0), anchor='w')
    
    result_text = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, width=70, height=20, 
                                            state=tk.DISABLED, **text_area_style)
    result_text.pack(pady=10, fill=tk.BOTH, expand=True)

    # テキストの色付け設定
    result_text.tag_config('header', foreground='yellow', font=(FONT[0], FONT[1], 'bold'))
    result_text.tag_config('term', foreground='light coral', font=(FONT[0], FONT[1], 'bold'))
    result_text.tag_config('info', foreground='gray', font=FONT)
    
    display_results([]) 

    root.mainloop()

if __name__ == "__main__":
    setup_gui()