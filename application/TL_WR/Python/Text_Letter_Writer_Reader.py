# Text_Letter_Writer_Reader.py
import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox, ttk
import os
import json 
from datetime import datetime

# --- 定数の定義 ---
BG_COLOR = 'gray20'
FG_COLOR = 'lime green' # メインの緑色
FONT_NAME = 'Meiryo UI' 
FONT_SIZE = 11
FONT = (FONT_NAME, FONT_SIZE)

# アプリケーションで使用するジャンルリスト (OptionMenu用)
GENRE_LIST = ["手紙", "計画書", "説明書", "契約書", "その他"] 

# --- グローバル変数 ---
# 左側エディタ用
text_title = None
text_date = None
text_body = None
text_signature = None
genre_var = None
confirm_text = None 
# 右側閲覧ビュー用
preview_text = None 
preview_area_frame = None 
current_folder_path = None 

# --- スプラッシュスクリーン関数 ---
def show_splash_screen(setup_main_gui_func):
    """
    スプラッシュスクリーンを表示し、一定時間後にそれを閉じ、
    メインGUI起動関数を呼び出します。
    """
    splash = tk.Tk()
    splash.overrideredirect(True) 
    splash.attributes('-topmost', True) 
    splash.config(bg=BG_COLOR) 

    # スプラッシュスクリーンのサイズと位置 (中央配置)
    splash_width = 700
    splash_height = 400
    screen_width = splash.winfo_screenwidth()
    screen_height = splash.winfo_screenheight()
    x = (screen_width // 2) - (splash_width // 2)
    y = (screen_height // 2) - (splash_height // 2)
    splash.geometry(f'{splash_width}x{splash_height}+{x}+{y}')

    # --- スプラッシュスクリーンのコンテンツ作成 ---
    logo_frame = tk.Frame(splash, bg=BG_COLOR)
    logo_frame.pack(expand=True, padx=40, pady=40)

    # テキストロゴ
    tk.Label(logo_frame, text="✍️ 📂", 
             font=("Segoe UI Emoji", 48, 'bold'), fg=FG_COLOR, bg=BG_COLOR).pack(side=tk.LEFT, padx=(0, 30))

    title_frame = tk.Frame(logo_frame, bg=BG_COLOR)
    title_frame.pack(side=tk.LEFT, anchor='center')

    tk.Label(title_frame, text="Text & Letter", 
             font=(FONT_NAME, FONT_SIZE + 20, 'bold'), fg=FG_COLOR, bg=BG_COLOR).pack(anchor='w')
    tk.Label(title_frame, text="Writer & Reader", 
             font=(FONT_NAME, FONT_SIZE + 15, 'bold'), fg=FG_COLOR, bg=BG_COLOR).pack(anchor='w')
    
    # バージョン情報
    tk.Label(splash, text="TLWR Version 1.2[Panther] (2025/11/20)", 
             font=(FONT_NAME, FONT_SIZE + 2, 'bold'), fg=FG_COLOR, bg=BG_COLOR).pack(side=tk.BOTTOM, anchor='se', padx=20, pady=10)

    def start_main_app():
        splash.destroy()      
        setup_main_gui_func() 

    # 3秒後にメインアプリを起動
    splash.after(3000, start_main_app) 

    splash.mainloop()
 


# --- 共通関数 ---
def update_confirmation_box(message, tag='normal'):
    """確認ボックスの内容を更新します。"""
    global confirm_text
    if confirm_text:
        confirm_text.config(state=tk.NORMAL)
        confirm_text.delete('1.0', tk.END)
        confirm_text.insert(tk.END, message, tag)
        confirm_text.config(state=tk.DISABLED)

def update_preview_text(content, content_type='text'):
    """右側の閲覧エリアの内容を更新します。（文字色：緑、書き換え不可）"""
    global preview_text, preview_area_frame
    
    # 既存のプレビューエリアの内容を全て破棄
    for widget in preview_area_frame.winfo_children():
        widget.destroy()

    # Textウィジェットを再構築
    preview_text = tk.Text(preview_area_frame, wrap=tk.WORD, **text_area_style, state=tk.DISABLED)
    
    vscroll_preview = ttk.Scrollbar(preview_area_frame, orient=tk.VERTICAL, command=preview_text.yview, style="TLWR.Vertical.TScrollbar")
    vscroll_preview.pack(side=tk.RIGHT, fill=tk.Y)
    preview_text.configure(yscrollcommand=vscroll_preview.set)

    preview_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # 内容の挿入
    preview_text.config(state=tk.NORMAL)
    preview_text.delete('1.0', tk.END)
    preview_text.insert(tk.END, content)
    
    preview_text.tag_config('title', foreground='light green', font=(FONT_NAME, FONT_SIZE + 2, 'bold'))
    preview_text.tag_config('header', foreground='yellow', font=(FONT_NAME, FONT_SIZE + 2, 'bold'))
    preview_text.tag_config('genre', foreground='yellow')
    
    preview_text.config(state=tk.DISABLED)

    # フォルダ内のファイル展開時に「閉じる」ボタンを表示
    if content_type == 'document':
        # Textウィジェットの上にフレームを重ねてボタンを表示
        close_frame = tk.Frame(preview_area_frame, bg='gray15')
        close_frame.place(relx=1.0, rely=0, anchor='ne') # 右上に配置
        
        close_button = tk.Button(close_frame, text="❌ 閉じる (一覧に戻る)", command=load_folder, 
                                 **_get_button_style('darkred')) # 赤系のボタン
        close_button.pack(padx=5, pady=5)


def format_document_preview(genre, title, date, body, signature):
    """単一の文書のプレビューコンテンツを整形します。"""
    formatted_body = body.replace('\n', '\n' + ' ' * 4) 
    
    return (
        f"--- 閲覧 / プレビュー ---\n\n"
        f"ジャンル: {genre}\n"
        f"タイトル: {title}\n"
        f"日付: {date}\n"
        f"\n"
        f"本文:\n"
        f"    {formatted_body}\n"
        f"\n"
        f"署名: {signature}"
    )

def _get_button_style(button_color='darkgreen'):
     # setup_gui 内のスタイル定義を再利用
     return {
        'bg': button_color, 'fg': FG_COLOR, 'font': (FONT_NAME, FONT_SIZE, 'bold'), 
        'activebackground': 'green', 'activeforeground': 'white', 'relief': tk.RAISED, 'bd': 2
    }
# --- 機能ロジック ---

def create_new_document():
    """入力フィールドを全てクリアし、新規作成の状態にします。（左側専用）"""
    global text_title, text_date, text_body, text_signature, genre_var
    
    text_title.delete(0, tk.END)
    text_date.delete(0, tk.END)
    text_body.delete('1.0', tk.END) 
    text_signature.delete(0, tk.END)
    
    if GENRE_LIST:
        genre_var.set(GENRE_LIST[0])
        
    current_date = datetime.now().strftime('%Y-%m-%d')
    text_date.insert(0, current_date)
    
    update_confirmation_box("✅ 新しい文書を作成しました。", 'success')


def load_document_content(filepath):
    """指定されたJSONファイルの内容を読み込み、プレビューテキストを更新します。"""
    global current_folder_path
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        filename = os.path.basename(filepath).replace('.json', '')
        
        # 🌟 修正点3: JSONからTitleを取得するように変更 🌟
        parsed_title = data.get('タイトル', 'N/A')
        
        # 署名、日付、ジャンル、本文をJSONから取得
        parsed_genre = data.get('ジャンル', 'N/A')
        parsed_date = data.get('日付', 'N/A')
        parsed_body = data.get('本文', 'N/A')
        parsed_signature = data.get('署名', 'N/A')
        
        # プレビューエリアの更新
        preview_content = format_document_preview(
            parsed_genre, parsed_title, parsed_date, parsed_body, parsed_signature
        )
        update_preview_text(preview_content, content_type='document')
        
        update_confirmation_box(f"✅ ファイル '{os.path.basename(filepath)}' を展開しました。", 'success')
        
    except FileNotFoundError:
        update_confirmation_box("❌ エラー: ファイルが見つかりません。", 'error')
    except json.JSONDecodeError:
        update_confirmation_box("❌ エラー: JSONファイルの形式が正しくありません。", 'error')
    except Exception as e:
        update_confirmation_box(f"❌ 予期せぬエラーが発生しました: {e}", 'error')


def load_document():
    """単一ファイル読み込み（File Readerボタン）のメイン関数"""
    
    filepath = filedialog.askopenfilename(
        defaultextension=".json",
        filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        title="文書JSONファイルを選択してください"
    )
    
    if not filepath:
        update_confirmation_box("📂 ファイルの選択がキャンセルされました。", 'info')
        return

    load_document_content(filepath)


def load_folder():
    """フォルダを選択し、中のJSONファイルリストを右側閲覧エリアにボタンとして表示します。（右側ボタン専用）"""
    global current_folder_path, preview_area_frame
    
    # current_folder_path があれば再利用、なければダイアログを開く
    if not current_folder_path or not os.path.isdir(current_folder_path):
        folderpath = filedialog.askdirectory(
            title="文書フォルダを選択してください"
        )
        if not folderpath:
            update_confirmation_box("📂 フォルダの選択がキャンセルされました。", 'info')
            return
        current_folder_path = folderpath
    
    folderpath = current_folder_path
    json_files = [f for f in os.listdir(folderpath) if f.endswith('.json')]
    
    # 既存のプレビューエリアの内容を全て破棄し、ボタン表示エリアに変更
    for widget in preview_area_frame.winfo_children():
        widget.destroy()

    if not json_files:
        update_confirmation_box("⚠️ 警告: 選択したフォルダに .json ファイルが見つかりませんでした。", 'warning')
        no_file_label = tk.Label(preview_area_frame, text=f"フォルダ名: {os.path.basename(folderpath)}\n\n.json ファイルはありませんでした。", bg=BG_COLOR, fg=FG_COLOR, font=FONT)
        no_file_label.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        return
        
    
    # スクロール可能なフレームを作成 (ボタンリスト用)
    canvas = tk.Canvas(preview_area_frame, bg='gray15', borderwidth=0, highlightthickness=0)
    vscroll = ttk.Scrollbar(preview_area_frame, orient="vertical", command=canvas.yview, style="TLWR.Vertical.TScrollbar")
    
    vscroll.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)
    canvas.configure(yscrollcommand=vscroll.set)
    
    # ボタンを配置する内部フレーム
    inner_frame = tk.Frame(canvas, bg='gray15')
    canvas.create_window((0, 0), window=inner_frame, anchor="nw")
    
    # ウィンドウサイズに合わせて内部フレームを調整する関数
    def on_frame_configure(event):
        canvas.configure(scrollregion=canvas.bbox("all"))
    
    inner_frame.bind("<Configure>", on_frame_configure)
    canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion = canvas.bbox("all")))
    
    # フォルダ読み込み結果のリストを作成
    header_label = tk.Label(inner_frame, text=f"--- フォルダ内容 ( {os.path.basename(folderpath)} ) ---\n項目数: {len(json_files)}件", 
                            bg='gray15', fg='yellow', font=FONT)
    header_label.pack(pady=(10, 5), padx=10, fill=tk.X)
    
    button_style = _get_button_style('gray30') # ボタンの背景を暗めに設定

    for i, filename in enumerate(json_files, 1):
        display_name = filename.replace('.json', '')
        filepath_full = os.path.join(folderpath, filename)
        
        # ボタンを押すと load_document_content 関数が呼ばれる
        button = tk.Button(inner_frame, text=f"[{i}] {display_name}", 
                           command=lambda fp=filepath_full: load_document_content(fp), 
                           **button_style)
        button.pack(pady=3, padx=10, fill=tk.X)


    update_confirmation_box(f"✅ フォルダ内容を読み込みました。\nフォルダ: {os.path.basename(folderpath)}\nJSONファイル数: {len(json_files)}件", 'success')


def save_document():
    """現在の入力内容をJSONファイルとして保存します。（左側専用）"""
    
    # 1. 内容の取得
    genre = genre_var.get().strip()
    title = text_title.get().strip() # 🌟 TitleをJSONに保存するため取得 🌟
    signature = text_signature.get().strip()
    body = text_body.get('1.0', tk.END).strip()
    
    # 🌟 修正点1: 現在の日時 (時/分/秒を含む) を取得 🌟
    current_datetime_obj = datetime.now()
    date_with_time = current_datetime_obj.strftime('%Y-%m-%d %H:%M:%S')
    date_for_filename = current_datetime_obj.strftime('%Y-%m-%d_%H-%M-%S') # ファイル名用の形式
    
    if not title or not signature:
        update_confirmation_box("⚠️ 警告: タイトルと署名は必須です。保存を中止しました。", 'warning')
        return

    # 2. JSONデータの作成 (Titleを追加し、日時を上書き)
    data_to_save = {
        "ジャンル": genre,
        "タイトル": title, # 🌟 TitleをJSONに保存 🌟
        "日付": date_with_time, # 時/分/秒を含む日時
        "本文": body,
        "署名": signature
    }
    
    # 3. ファイル名の作成: [ジャンル]_[署名]_[日時].json
    # 署名が[著者]に相当し、ファイル名に含める
    initial_file_name = f"{genre}_{signature}_{date_for_filename}.json"
    
    # 4. ファイルダイアログを表示
    filepath = filedialog.asksaveasfilename(
        defaultextension=".json",
        filetypes=[("JSON files", "*.json")],
        title="ファイルを保存",
        initialfile=initial_file_name 
    )
    
    if not filepath:
        update_confirmation_box("📂 ファイルの保存がキャンセルされました。", 'info')
        return

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=4)
            
        update_confirmation_box(f"✅ 文書を正常にJSON形式で保存しました。\nファイル名: {os.path.basename(filepath)}", 'success')
        
    except Exception as e:
        update_confirmation_box(f"❌ エラー: ファイルの保存に失敗しました。\nエラー内容: {e}", 'error')


# --- GUIのセットアップ (左右分割ビュー) ---

def setup_gui():
    global text_title, text_date, text_body, text_signature, genre_var, confirm_text, preview_text, preview_area_frame
    
    root = tk.Tk()
    root.title("Text&Letter Writer&Reader") 
    root.configure(bg=BG_COLOR)
    
    # 🌟 スクロールバーのスタイル設定 🌟
    style = ttk.Style(root)
    style.theme_use('clam')
    
    scroll_style_name = "TLWR.Vertical.TScrollbar"
    style.configure(scroll_style_name, 
                    background='gray30',         # トラックの色 (暗い背景)
                    troughcolor='gray15',        # トラックの背景色
                    bordercolor='gray30',
                    arrowcolor=FG_COLOR,         # 矢印の色 (緑)
                    )
    style.map(scroll_style_name,
              background=[('active', 'gray40')], # ホバー時のトラックの色
              relief=[('pressed', 'sunken'), ('!active', 'flat')]
              )

    window_width = 1200 
    window_height = 800
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x_cordinate = (screen_width // 2) - (window_width // 2)
    y_cordinate = (screen_height // 2) - (window_height // 2)
    root.geometry(f'{window_width}x{window_height}+{x_cordinate}+{y_cordinate}')
    
    # --- スタイル設定 ---
    label_style = {'bg': BG_COLOR, 'fg': FG_COLOR, 'font': FONT}
    entry_style = {'bg': 'gray15', 'fg': FG_COLOR, 'insertbackground': FG_COLOR, 'font': FONT, 'relief': tk.SOLID, 'bd': 1}
    button_style = {'bg': 'darkgreen', 'fg': FG_COLOR, 'font': (FONT_NAME, FONT_SIZE, 'bold'), 'activebackground': 'green', 'activeforeground': 'white', 'relief': tk.RAISED, 'bd': 2}
    
    # エディタ/閲覧エリアのスタイル（緑色の文字）
    global text_area_style
    text_area_style = {'bg': 'gray15', 'fg': FG_COLOR, 'font': ('Consolas', 12), 'relief': tk.SUNKEN, 'bd': 2, 'insertbackground': FG_COLOR}
    
    option_menu_style = {
        'bg': 'gray15', 'fg': FG_COLOR, 'font': FONT,
        'activebackground': 'darkgreen', 'activeforeground': 'white',    
        'relief': tk.SOLID, 'bd': 1, 'width': 15 
    }
    
    # --- PanedWindow (左右分割) ---
    paned_window = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
    paned_window.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # --- A. 左側フレーム (エディタ/作成・保存専用) ---
    left_frame = tk.Frame(paned_window, bg=BG_COLOR, padx=15, pady=15)
    paned_window.add(left_frame, weight=1) 
    
    # 1. アクションボタン群 (新規作成/保存 のみ)
    button_frame = tk.Frame(left_frame, bg=BG_COLOR)
    button_frame.pack(pady=(0, 15), fill=tk.X)
    
    tk.Button(button_frame, text="📄 新規作成", command=create_new_document, **button_style).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
    tk.Button(button_frame, text="💾 JSON保存", command=save_document, **button_style).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5, 0))

    # 2. メタデータ入力
    
    tk.Label(left_frame, text="Title:", **label_style).pack(pady=(5, 2), anchor='w') 
    text_title = tk.Entry(left_frame, width=80, **entry_style)
    text_title.pack(fill=tk.X)

    tk.Label(left_frame, text="Genre Date:", **label_style).pack(pady=(10, 2), anchor='w') 
    date_genre_frame = tk.Frame(left_frame, bg=BG_COLOR)
    date_genre_frame.pack(fill=tk.X)
    
    # 日付 (保存時に上書きされるが、初期表示用として残す)
    text_date = tk.Entry(date_genre_frame, width=15, **entry_style)
    text_date.insert(0, datetime.now().strftime('%Y-%m-%d'))
    text_date.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    # ジャンル
    genre_var = tk.StringVar(root)
    genre_var.set(GENRE_LIST[0]) 
    option_menu = tk.OptionMenu(date_genre_frame, genre_var, *GENRE_LIST)
    option_menu.config(**option_menu_style)
    menu = root.nametowidget(option_menu.menuname)
    menu.config(bg='gray15', fg='lime green', font=FONT, activebackground='darkgreen', activeforeground='white')
    option_menu.pack(side=tk.RIGHT, padx=(10, 0))
    
    tk.Label(left_frame, text="text (本文):", **label_style).pack(pady=(10, 2), anchor='w') 
    
    # Text+ttk.Scrollbar
    text_body_frame = tk.Frame(left_frame, bg=BG_COLOR)
    text_body_frame.pack(pady=(0, 10), fill=tk.BOTH, expand=True)

    text_body = tk.Text(text_body_frame, wrap=tk.WORD, height=15, **text_area_style)
    
    vscroll_body = ttk.Scrollbar(text_body_frame, orient=tk.VERTICAL, command=text_body.yview, style=scroll_style_name)
    vscroll_body.pack(side=tk.RIGHT, fill=tk.Y)
    text_body.configure(yscrollcommand=vscroll_body.set)

    text_body.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    tk.Label(left_frame, text="Name (署名):", **label_style).pack(pady=(5, 2), anchor='w') 
    text_signature = tk.Entry(left_frame, width=80, **entry_style)
    text_signature.pack(fill=tk.X)

    # 3. 確認ボックス
    tk.Label(left_frame, text="--- 状況 / メッセージ ---", **label_style).pack(pady=(10, 0), anchor='w')
    
    # 確認ボックスにもText+ttk.Scrollbarを使用
    confirm_text_frame = tk.Frame(left_frame, bg=BG_COLOR)
    confirm_text_frame.pack(pady=5, fill=tk.X)

    confirm_text = tk.Text(confirm_text_frame, wrap=tk.WORD, height=3, **text_area_style, state=tk.DISABLED)
    vscroll_confirm = ttk.Scrollbar(confirm_text_frame, orient=tk.VERTICAL, command=confirm_text.yview, style=scroll_style_name)
    vscroll_confirm.pack(side=tk.RIGHT, fill=tk.Y)
    confirm_text.configure(yscrollcommand=vscroll_confirm.set)
    confirm_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    confirm_text.tag_config('error', foreground='red')
    confirm_text.tag_config('info', foreground='gray')
    confirm_text.tag_config('warning', foreground='yellow')
    confirm_text.tag_config('success', foreground=FG_COLOR, font=(FONT_NAME, FONT_SIZE, 'bold'))

    # --- B. 右側フレーム (閲覧/ファイル読み込み専用) ---
    right_frame = tk.Frame(paned_window, bg=BG_COLOR, padx=15, pady=15)
    paned_window.add(right_frame, weight=1) 

    # 1. アクションボタン群 (ファイル読み込み / フォルダ読み込み)
    right_button_frame = tk.Frame(right_frame, bg=BG_COLOR)
    right_button_frame.pack(pady=(0, 15), fill=tk.X)
    
    tk.Button(right_button_frame, text="📂 File Reader", command=load_document, **button_style).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
    tk.Button(right_button_frame, text="📁 フォルダ読み込み", command=load_folder, **button_style).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5, 0))
    
    tk.Label(right_frame, text="➡️ 閲覧 / プレビュー画面", font=(FONT_NAME, FONT_SIZE + 4, 'bold'), fg='light green', bg=BG_COLOR).pack(pady=10)
    
    # 2. 閲覧エリア (動的にTextウィジェットを格納するためのフレーム)
    preview_area_frame = tk.Frame(right_frame, bg=BG_COLOR)
    preview_area_frame.pack(pady=5, fill=tk.BOTH, expand=True)
    
    # 起動時、右の内容を空白にする
    update_preview_text("")
    
    root.mainloop()

if __name__ == "__main__":
    show_splash_screen(setup_gui)