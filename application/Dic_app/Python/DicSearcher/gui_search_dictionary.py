# gui_search_dictionary.py
import json 
import os
import tkinter as tk
from tkinter import filedialog, scrolledtext, ttk
# --- Pillow (PIL Fork) のインポート ---
# 画像を使用する場合は、'pip install Pillow' でインストールが必要です
from PIL import Image, ImageTk 
import sys # 👈 追加: PyInstallerでのパス処理に必要
import os  # 👈 追加: パス処理に必要

# constants.py からのインポート
from constants import DATA_FILE, FONT_SIZE, BG_COLOR, FG_COLOR, FONT, DICTIONARY_FIELDS

# --- PyInstallerリソースパス関数 (配布用に追加) ---
def resource_path(relative_path):
    """PyInstallerでバンドルされたリソースの絶対パスを返す"""
    try:
        # PyInstallerが生成した一時フォルダのパスを取得
        base_path = sys._MEIPASS
    except Exception:
        # スクリプトとして実行されている場合のベースパス
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# グローバル変数として読み込んだ全データを保持
loaded_data = []
loaded_filepath = "" 

# ウィジェットをグローバルで保持
result_text = None
search_entry = None
search_scope_var = None 
confirm_text = None 
# 現在の検索モードを保持 (デフォルトは 'normal')
search_mode = 'normal' 

# --- スプラッシュスクリーン関数 (画像ロゴ対応) ---
def show_splash_screen(setup_main_gui_func):
    """
    スプラッシュスクリーンを表示し、一定時間後にそれを閉じ、
    メインGUI起動関数 (setup_main_gui_func) を呼び出します。
    """
    splash = tk.Tk()
    splash.overrideredirect(True) 
    splash.attributes('-topmost', True) 
    splash.config(bg=BG_COLOR) 

    # スプラッシュスクリーンのサイズと位置 (中央配置)
    splash_width = 800
    splash_height = 450
    screen_width = splash.winfo_screenwidth()
    screen_height = splash.winfo_screenheight()
    x = (screen_width // 2) - (splash_width // 2)
    y = (screen_height // 2) - (splash_height // 2)
    splash.geometry(f'{splash_width}x{splash_height}+{x}+{y}')

    # --- スプラッシュスクリーンのコンテンツ作成 ---
    logo_frame = tk.Frame(splash, bg=BG_COLOR)
    logo_frame.pack(expand=True, padx=50, pady=50)

    # 🌟 画像ロゴの表示 (resource_pathを使用するように修正) 🌟
    logo_image_path = resource_path("logo.png") 
    logo_label = None 

    try:
        # 画像を読み込み、Tkinterで表示可能な形式に変換
        original_image = Image.open(logo_image_path)
        
        # サイズ調整 (幅250pxに調整)
        img_width = 250
        img_height = int(img_width * (original_image.height / original_image.width))
        resized_image = original_image.resize((img_width, img_height), Image.Resampling.LANCZOS)
        
        logo_image_tk = ImageTk.PhotoImage(resized_image)
        
        logo_label = tk.Label(logo_frame, image=logo_image_tk, bg=BG_COLOR)
        logo_label.image = logo_image_tk 
        logo_label.pack(side=tk.LEFT, padx=(0, 20))

    except FileNotFoundError:
        print(f"警告: ロゴ画像ファイル '{logo_image_path}' が見つかりませんでした。テキストロゴで代替します。")
        # 画像が見つからない場合はテキストロゴで代替
        tk.Label(logo_frame, text="📚📚📚\n📚📚📚\n📚📚📚", 
                 font=("Segoe UI Emoji", 36, 'bold'), fg=FG_COLOR, bg=BG_COLOR).pack(side=tk.LEFT, padx=(0, 20))
    except Exception as e:
        print(f"警告: ロゴ画像の読み込み中にエラーが発生しました: {e}。テキストロゴで代替します。")
        # その他のエラーが発生した場合もテキストロゴで代替
        tk.Label(logo_frame, text="📚📚📚\n📚📚📚\n📚📚📚", 
                 font=("Segoe UI Emoji", 36, 'bold'), fg=FG_COLOR, bg=BG_COLOR).pack(side=tk.LEFT, padx=(0, 20))


    title_frame = tk.Frame(logo_frame, bg=BG_COLOR)
    title_frame.pack(side=tk.LEFT, anchor='center')

    tk.Label(title_frame, text="Dictionary", 
             font=(FONT[0], FONT_SIZE + 20, 'bold'), fg=FG_COLOR, bg=BG_COLOR).pack(anchor='w')
    tk.Label(title_frame, text="Searcher", 
             font=(FONT[0], FONT_SIZE + 20, 'bold'), fg=FG_COLOR, bg=BG_COLOR).pack(anchor='w')
    
    # バージョン情報 
    tk.Label(splash, text="Version 1.2[Dogfight] (2025/11/19)", 
             font=(FONT[0], FONT_SIZE + 2, 'bold'), fg=FG_COLOR, bg=BG_COLOR).pack(side=tk.BOTTOM, anchor='se', padx=20, pady=10)

    def start_main_app():
        splash.destroy()      
        setup_main_gui_func() 

    splash.after(3000, start_main_app) 

    splash.mainloop()
 


# --- 共通関数 ---
def update_confirmation_box(message, tag='normal'):
    """確認ボックスの内容を更新します。"""
    global confirm_text
    if confirm_text:
        confirm_text.config(state=tk.NORMAL)
        confirm_text.delete(1.0, tk.END)
        confirm_text.insert(tk.END, message, tag)
        confirm_text.config(state=tk.DISABLED)

# --- データ操作ロジック ---

def _load_data_logic(filepath, silent=False):
    """データ読み込みのコアロジック。"""
    global loaded_data, loaded_filepath
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        
        loaded_filepath = filepath
        if not silent:
            update_confirmation_box(
                f"✅ データが正常に読み込まれました。\nファイル: {os.path.basename(filepath)}\n項目数: {len(loaded_data)}件", 
                'success'
            )
        
        search_and_display()
        return True
        
    except FileNotFoundError:
        if not silent:
            update_confirmation_box("❌ エラー: ファイルが見つかりません。", 'error')
        loaded_data = []
        loaded_filepath = ""
    except json.JSONDecodeError:
        if not silent:
            update_confirmation_box("❌ エラー: JSONファイルの形式が正しくありません。", 'error')
        loaded_data = []
        loaded_filepath = ""
    except Exception as e:
        if not silent:
            update_confirmation_box(f"❌ 予期せぬエラーが発生しました: {e}", 'error')
        loaded_data = []
        loaded_filepath = ""
    
    display_results([])
    return False

def load_data_default():
    """デフォルトのDATA_FILEからデータを読み込みを試みます。"""
    if os.path.exists(DATA_FILE):
        _load_data_logic(DATA_FILE, silent=True)
        if loaded_data:
            update_confirmation_box(
                f"✅ 起動時にデフォルトファイルが読み込まれました。\nファイル: {DATA_FILE}\n項目数: {len(loaded_data)}件", 
                'success'
            )
    else:
        update_confirmation_box(f"「データ読み込み」ボタンを押して、辞書データファイルを選択してください。（デフォルトファイル: {DATA_FILE} が見つかりませんでした）", 'normal')


def load_data_from_file_dialog():
    """ファイル選択ダイアログを表示し、JSONファイルを読み込みます。"""
    
    initialdir = os.path.dirname(loaded_filepath) if loaded_filepath else os.getcwd()

    filepath = filedialog.askopenfilename(
        defaultextension=".json",
        filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        title="辞書データファイルを選択してください",
        initialdir=initialdir
    )
    
    if not filepath:
        update_confirmation_box("📂 ファイルの選択がキャンセルされました。", 'info')
        return

    _load_data_logic(filepath)

# --- 検索モード設定のラッパー関数 ---
def set_search_mode_and_run(mode):
    """グローバルな検索モードを設定し、検索関数を呼び出します。"""
    global search_mode
    search_mode = mode
    search_and_display()

# --- 検索ロジック ---
def search_and_display(event=None):
    """検索ボックスの入力と検索ジャンルに基づいてデータをフィルタリングし、結果を表示します。"""
    global search_scope_var, search_mode 
    
    if not loaded_data:
        display_results([])
        return
        
    search_term = search_entry.get().lower().strip()
    selected_scope_display = search_scope_var.get()
    
    scope_map = {v: k for k, v in DICTIONARY_FIELDS.items()} 
    
    if selected_scope_display == "全項目":
        search_keys = list(DICTIONARY_FIELDS.keys())
    else:
        search_keys = [scope_map.get(selected_scope_display)]

    if not search_term:
        display_results(loaded_data)
        search_mode = 'normal' 
        return
    
    current_mode = search_mode 
    results = []
    
    for entry in loaded_data:
        if not search_keys or search_keys[0] is None: 
             continue 

        found = False
        for key in search_keys:
            entry_value = str(entry.get(key, '')).lower()
            
            if current_mode == 'start_with':
                if entry_value.startswith(search_term):
                    results.append(entry)
                    found = True
                    break
            
            elif current_mode == 'end_with':
                if entry_value.endswith(search_term):
                    results.append(entry)
                    found = True
                    break
                    
            else: # 'normal' (含む検索)
                if search_term in entry_value: 
                    results.append(entry)
                    found = True
                    break
            
    display_results(results, search_term, current_mode)
    
    search_mode = 'normal' 

def display_results(results, search_term="", mode='normal'):
    """指定されたデータを結果表示エリアに整形して出力します。(モード表示を追加)"""
    result_text.config(state=tk.NORMAL)
    result_text.delete(1.0, tk.END)
    
    if not loaded_data and not results:
        result_text.insert(tk.END, "データを読み込んでください。", 'info')
    elif not results and search_term:
        
        mode_text = ""
        if mode == 'start_with':
            mode_text = "(最初の文字検索)"
        elif mode == 'end_with':
            mode_text = "(最後の文字検索)"
            
        result_text.insert(tk.END, f"キーワード「{search_term}」に一致する項目は見つかりませんでした {mode_text}", 'info')
        
    elif not results and not search_term and loaded_data:
         result_text.insert(tk.END, "キーワードを入力するか、全項目が表示されています。", 'info')
    elif not results and not search_term and not loaded_data:
         result_text.insert(tk.END, "データが読み込まれていません。", 'info')
    else:
        mode_text = "（含む）"
        if mode == 'start_with':
            mode_text = "（最初の文字検索）"
        elif mode == 'end_with':
            mode_text = "（最後の文字検索）"

        header_text = f"--- 表示項目数: {len(results)}件 {mode_text} (全{len(loaded_data)}件中) ---\n\n"
        
        result_text.insert(tk.END, header_text, 'header')
        
        for i, result in enumerate(results, 1):
            result_text.insert(tk.END, f"[{i}] 単語: {result.get('term', 'N/A')}\n", 'term')
            result_text.insert(tk.END, f"  発音: {result.get('pronunciation', 'N/A')}\n")
            result_text.insert(tk.END, f"  意味・定義: {result.get('definition', 'N/A')}\n")
            result_text.insert(tk.END, f"  品詞: {result.get('part_of_speech', 'N/A')}\n")
            result_text.insert(tk.END, f"  使用例: {result.get('example', 'N/A')}\n\n")

    result_text.config(state=tk.DISABLED)

# --- GUIの構築とデザイン設定 ---
def setup_gui():
    
    global search_entry, result_text, search_scope_var, confirm_text
    
    root = tk.Tk()
    root.title("DicSearcher V1.2[DogFight]")
    root.configure(bg=BG_COLOR)
    
    # ウィンドウを中央に配置するロジック
    window_width = 800
    window_height = 650

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    x_cordinate = (screen_width // 2) - (window_width // 2)
    y_cordinate = (screen_height // 2) - (window_height // 2)

    root.geometry(f'{window_width}x{window_height}+{x_cordinate}+{y_cordinate}')
    
    style = ttk.Style()
    style.theme_use('clam')
    
    label_style = {'bg': BG_COLOR, 'fg': FG_COLOR, 'font': FONT}
    entry_style = {'bg': 'gray15', 'fg': FG_COLOR, 'insertbackground': FG_COLOR, 'font': FONT, 'relief': tk.SOLID, 'bd': 1}
    button_style = {'bg': 'darkgreen', 'fg': FG_COLOR, 'font': (FONT[0], FONT_SIZE, 'bold'), 'activebackground': 'green', 'activeforeground': 'white', 'relief': tk.RAISED, 'bd': 2}
    text_area_style = {'bg': 'gray15', 'fg': FG_COLOR, 'font': FONT, 'relief': tk.SUNKEN, 'bd': 2, 'insertbackground': FG_COLOR}
    
    option_menu_style = {
        'bg': 'gray15', 'fg': FG_COLOR, 'font': FONT,
        'activebackground': 'darkgreen', 'activeforeground': 'white',    
        'indicatoron': 0, 'width': 20, 'relief': tk.SOLID, 'bd': 1
    }
    
    main_frame = tk.Frame(root, bg=BG_COLOR, padx=10, pady=10)
    main_frame.pack(expand=True, fill=tk.BOTH)

    # 1. データ読み込みボタン
    load_button = tk.Button(main_frame, text="📂 データ読み込み (ファイル選択)", command=load_data_from_file_dialog, **button_style)
    load_button.pack(pady=(0, 10), fill=tk.X)

    # 2. 検索コントロールフレーム (OptionMenuとEntryを配置)
    control_frame = tk.Frame(main_frame, bg=BG_COLOR)
    control_frame.pack(pady=5, fill=tk.X)
    
    tk.Label(control_frame, text="🔍 検索ジャンル:", **label_style).pack(side=tk.LEFT, padx=(0, 5))

    search_scopes = ["全項目"] + list(DICTIONARY_FIELDS.values())
    search_scope_var = tk.StringVar(root)
    search_scope_var.set(search_scopes[0]) 

    search_menu = tk.OptionMenu(control_frame, search_scope_var, *search_scopes, command=search_and_display)
    search_menu.config(**option_menu_style)
    
    menu = root.nametowidget(search_menu.menuname)
    menu.config(
        bg='gray15', fg='lime green', font=FONT,
        activebackground='darkgreen', activeforeground='white'
    )
    
    search_menu.pack(side=tk.LEFT, padx=(0, 10))

    search_entry = tk.Entry(control_frame, width=30, **entry_style)
    search_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)
    search_entry.bind('<KeyRelease>', search_and_display)

    button_frame = tk.Frame(main_frame, bg=BG_COLOR)
    button_frame.pack(pady=(5, 10), fill=tk.X)
    
    start_button = tk.Button(button_frame, text="▶️ 最初の文字検索", 
                             command=lambda: set_search_mode_and_run('start_with'), **button_style)
    start_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
    
    end_button = tk.Button(button_frame, text="🔚 最後の文字検索", 
                           command=lambda: set_search_mode_and_run('end_with'), **button_style)
    end_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5, 0))

    # --- 確認ボックスの追加 (ロードメッセージ用) --- 
    tk.Label(main_frame, text="--- 状況 / メッセージ ---", **label_style).pack(pady=(10, 0), anchor='w')
    
    confirm_text = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, height=3, 
                                            bg='gray15', fg='lime green', font=('Consolas', 12), 
                                            relief=tk.SUNKEN, bd=2, insertbackground='lime green', state=tk.DISABLED)
    confirm_text.pack(pady=5, fill=tk.X)
    
    confirm_text.tag_config('error', foreground='red')
    confirm_text.tag_config('info', foreground='gray')
    confirm_text.tag_config('success', foreground=FG_COLOR, font=(FONT[0], FONT_SIZE, 'bold'))
    
    # 3. 検索結果表示エリア
    tk.Label(main_frame, text="--- データ一覧 / 検索結果 ---", **label_style).pack(pady=(10, 0), anchor='w')
    
    result_text = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, width=70, height=15, 
                                            state=tk.DISABLED, **text_area_style)
    result_text.pack(pady=10, fill=tk.BOTH, expand=True)

    result_text.tag_config('header', foreground='yellow', font=(FONT[0], FONT[1], 'bold'))
    result_text.tag_config('term', foreground='light coral', font=(FONT[0], FONT[1], 'bold'))
    
    load_data_default() 

    root.mainloop()

if __name__ == "__main__":
    show_splash_screen(setup_gui)