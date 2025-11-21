# Text_Letter_Writer_Reader.py (句読点変換機能 復活版)
import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox, ttk, simpledialog
import os
import json 
from datetime import datetime
import re 
from collections import defaultdict
import os 

# --- 定数の定義 ---
BG_COLOR = 'gray20'
FG_COLOR = 'lime green' 
FONT_NAME = 'Meiryo UI' 
FONT_SIZE = 11
FONT = (FONT_NAME, FONT_SIZE)

GENRE_LIST = ["手紙", "計画書", "説明書", "契約書", "その他"] 
CONFIG_FILE = 'tlwr_config.json' 
HISTORY_MAX = 10 

TEMPLATES = {
    "手紙": { "body": "拝啓\n\n[本文をここに記入してください。季節の挨拶や用件]\n\n敬具", "signature": "氏名" },
    "計画書": { "body": "## プロジェクト概要\n\n目的: \n期間: \n\n## 実施項目\n\n1. \n2. \n", "signature": "担当者名" },
    "説明書": { "body": "【製品名】取扱説明書\n\n1. はじめに\n\n2. 使用方法\n\n", "signature": "作成者" },
    "契約書": { "body": "第1条 (目的)\n\n第2条 (期間)\n\n上記内容に合意する。", "signature": "甲・乙" },
    "その他": { "body": "", "signature": "著者" }
}
INVALID_FILENAME_CHARS = r'[\\/:*?"<>|]'


# --- グローバル変数 ---
text_title = None 
text_date = None
text_body = None
text_signature = None 
genre_var = None
confirm_text = None 
preview_text = None 
preview_area_frame = None 
current_folder_path = None 
title_history = []
signature_history = []
search_entry = None
sort_var = None
current_json_data = [] 
current_json_file_paths = [] 
notebook = None 
active_genre_filter = "すべて"
tab_list_frames = {} 
current_editing_filepath = None
current_doc_date_time = None 
count_label = None 
# 設定変数
app_settings = {
    'default_load_path': None,
    'default_save_path': None,
    'use_config_file': True,
    'last_selected_config': CONFIG_FILE,
    'disable_splash_screen': False, 
}

# --- 設定ファイルの読み書き ---
def load_config():
    global title_history, signature_history, current_folder_path, app_settings
    
    # 🌟 修正: CONFIG_FILEが設定されている場合、絶対パスに変換 🌟
    if app_settings.get('last_selected_config') == CONFIG_FILE:
        app_settings['last_selected_config'] = os.path.abspath(CONFIG_FILE)

    config_to_load = app_settings['last_selected_config'] if app_settings.get('use_config_file', True) else CONFIG_FILE
    
    if os.path.exists(config_to_load):
        try:
            with open(config_to_load, 'r', encoding='utf-8') as f:
                config = json.load(f)
                title_history = config.get('title_history', [])
                signature_history = config.get('signature_history', [])
                current_folder_path = config.get('current_folder', None)
                
                app_settings['default_load_path'] = config.get('default_load_path')
                app_settings['default_save_path'] = config.get('default_save_path')
                app_settings['use_config_file'] = config.get('use_config_file', True)
                app_settings['last_selected_config'] = config.get('last_selected_config', CONFIG_FILE)
                app_settings['disable_splash_screen'] = config.get('disable_splash_screen', False)
                
        except Exception:
            pass

def save_config():
    global title_history, signature_history, current_folder_path, app_settings
    
    title_history = list(dict.fromkeys(title_history))[:HISTORY_MAX]
    signature_history = list(dict.fromkeys(signature_history))[:HISTORY_MAX]
    
    config = {
        'title_history': title_history,
        'signature_history': signature_history,
        'current_folder': current_folder_path,
        'default_load_path': app_settings['default_load_path'],
        'default_save_path': app_settings['default_save_path'],
        'use_config_file': app_settings['use_config_file'],
        'last_selected_config': app_settings['last_selected_config'],
        'disable_splash_screen': app_settings['disable_splash_screen'],
    }
    
    config_file_to_save = app_settings['last_selected_config'] if app_settings.get('use_config_file', True) else CONFIG_FILE
    
    try:
        with open(config_file_to_save, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
    except Exception as e:
        update_confirmation_box(f"❌ 設定ファイル保存エラー: {e}", 'error')


# --- 共通関数 ---
def update_confirmation_box(message, tag='normal'):
    global confirm_text
    if confirm_text:
        confirm_text.config(state=tk.NORMAL)
        confirm_text.delete('1.0', tk.END)
        confirm_text.insert(tk.END, message, tag)
        confirm_text.config(state=tk.DISABLED)

def _get_button_style(button_color='darkgreen'):
     return {
        'bg': button_color, 'fg': FG_COLOR, 'font': (FONT_NAME, FONT_SIZE, 'bold'), 
        'activebackground': 'green', 'activeforeground': 'white', 'relief': tk.RAISED, 'bd': 2
    }
    
def update_preview_text(content, content_type='text', filepath=None):
    """右側の閲覧エリアの内容を更新します。（文字色：緑、書き換え不可）"""
    global preview_text, preview_area_frame

    for widget in preview_area_frame.winfo_children():
        widget.destroy()

    preview_frame = tk.Frame(preview_area_frame, bg=BG_COLOR)
    preview_frame.pack(pady=5, fill=tk.BOTH, expand=True)

    preview_text = tk.Text(preview_frame, wrap=tk.WORD, **text_area_style, state=tk.DISABLED)
    vscroll_preview = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=preview_text.yview, style="TLWR.Vertical.TScrollbar")
    vscroll_preview.pack(side=tk.RIGHT, fill=tk.Y)
    preview_text.configure(yscrollcommand=vscroll_preview.set)
    preview_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    button_tray = tk.Frame(preview_frame, bg='gray15')
    button_tray.place(relx=1.0, rely=0, anchor='ne')

    close_button = tk.Button(button_tray, text="❌ 閉じる (一覧に戻る)", 
                             command=load_folder_view, 
                             **_get_button_style('darkred')) 
    close_button.pack(side=tk.RIGHT, padx=5, pady=5)
    
    if content_type == 'document' and filepath:
        edit_button = tk.Button(button_tray, text="📝 エディタにロード (編集)", 
                                 command=lambda fp=filepath: load_document_to_editor(fp),
                                 **_get_button_style('darkorange'))
        edit_button.pack(side=tk.RIGHT, padx=(0, 5), pady=5)
    
    preview_text.config(state=tk.NORMAL)
    preview_text.delete('1.0', tk.END)
    preview_text.insert(tk.END, content)
    
    preview_text.tag_config('title', foreground='light green', font=(FONT_NAME, FONT_SIZE + 2, 'bold'))
    preview_text.tag_config('header', foreground='yellow', font=(FONT_NAME, FONT_SIZE + 2, 'bold'))
    preview_text.tag_config('genre', foreground='yellow')
    
    preview_text.config(state=tk.DISABLED)


def format_document_preview(genre, title, date, body, signature):
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

# 🌟 句読点変換機能の復活 🌟
def convert_punctuation(event):
    """本文エリアの「、」を「,」に、「。」を「.」に自動変換します。"""
    global text_body
    
    # 句読点「、」「。」が押された時のみ実行
    if event.char in ['、', '。']:
        
        # カーソルが1文字分挿入された状態（Textウィジェットのデフォルト動作）を避けるため、
        # <Key>イベントで処理し、Textウィジェットのデフォルト動作（文字挿入）を抑制（return 'break'）する。
        # 代わりに、手動でカーソル直前に変換した文字を挿入する。
        
        # event.charが '、' の場合、',' を挿入。'。' の場合、'.' を挿入。
        replacement_char = ',' if event.char == '、' else '.'
        
        try:
            # 現在のカーソル位置を取得
            current_index = text_body.index(tk.INSERT)
            
            # 変換文字をカーソル位置に挿入
            text_body.insert(current_index, replacement_char)
            
            # カーソルを1文字分進める
            text_body.mark_set(tk.INSERT, f"{current_index}+1c")
            
        except Exception as e:
            # エラー処理。変換がうまくいかない場合、何もしない
            pass
            
        # Textウィジェットのデフォルトの文字挿入動作を抑制
        # KeyReleaseイベントで文字数カウントとバリデーションを別途実行する
        return 'break'
        
    # 句読点以外の場合は、デフォルトのキー動作を許可し、KeyReleaseイベントで後処理
    return None 

def update_text_count(event=None):
    """本文エリアの文字数と行数をリアルタイムで更新します。"""
    global text_body, count_label
    
    if not text_body or not count_label:
        return

    content = text_body.get('1.0', tk.END).strip()
    
    char_count = len(content.replace(" ", "").replace("\n", ""))
    
    if not content:
        line_count = 1
    else:
        line_count = int(text_body.index(tk.END).split('.')[0]) - 1
        if line_count == 0:
            line_count = 1

    count_label.config(text=f"文字数: {char_count} | 行数: {line_count}")


def validate_input(event=None):
    title = text_title.get()
    signature = text_signature.get()
    
    invalid_chars_title = re.findall(INVALID_FILENAME_CHARS, title)
    invalid_chars_signature = re.findall(INVALID_FILENAME_CHARS, signature)
    
    warning_message = ""
    
    # ttk.ComboboxはStringVarを使用していないため、configureでfgを設定
    fg_color_config = {'foreground': 'red'} if invalid_chars_title else {'foreground': FG_COLOR}
    text_title.configure(**fg_color_config)
        
    fg_color_config = {'foreground': 'red'} if invalid_chars_signature else {'foreground': FG_COLOR}
    text_signature.configure(**fg_color_config)

    if invalid_chars_title:
        warning_message += f"タイトルにファイル名に使えない文字 ('{', '.join(set(invalid_chars_title))}') が含まれています。\n"
    if invalid_chars_signature:
        warning_message += f"署名にファイル名に使えない文字 ('{', '.join(set(invalid_chars_signature))}') が含まれています。"

    if warning_message:
        update_confirmation_box("⚠️ ファイル名に使えない特殊文字があります。保存エラーの原因になります。\n" + warning_message, 'error')
        return False
    else:
        # 警告がなくなったときにメッセージを更新
        current_msg = confirm_text.get('1.0', tk.END).strip()
        # 警告やエラーメッセージが含まれていれば、正常メッセージで上書きする
        if "特殊文字" in current_msg or "警告" in current_msg or "エラー" in current_msg:
            update_confirmation_box("✅ 入力に問題ありません。", 'success')
        return True
        
def apply_template():
    genre = genre_var.get()
    
    if genre in TEMPLATES:
        template = TEMPLATES[genre]
        
        text_body.delete('1.0', tk.END)
        text_body.insert('1.0', template['body'])
        
        text_signature.delete(0, tk.END)
        text_signature.insert(0, template['signature'])
        
        update_confirmation_box(f"✅ ジャンル '{genre}' のテンプレートを適用しました。", 'info')
        update_text_count() 
    else:
        update_confirmation_box("⚠️ 選択されたジャンルにテンプレートがありません。", 'warning')

def create_new_document():
    global text_title, text_date, text_body, text_signature, genre_var, current_editing_filepath, current_doc_date_time
    
    current_editing_filepath = None
    current_doc_date_time = None
    
    text_title.set('')
    text_signature.set('')
    
    text_body.delete('1.0', tk.END) 
    
    if GENRE_LIST:
        genre_var.set(GENRE_LIST[0])
        
    current_date = datetime.now().strftime('%Y-%m-%d')
    text_date.config(state=tk.NORMAL)
    text_date.delete(0, tk.END)
    text_date.insert(0, current_date)
    text_date.config(state=tk.DISABLED)

    update_confirmation_box("✅ 新しい文書を作成しました。", 'success')
    update_text_count() 

def load_document_to_editor(filepath):
    global current_editing_filepath, current_doc_date_time
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        current_editing_filepath = filepath
        current_doc_date_time = data.get('日付') 
        
        if current_doc_date_time is None:
             current_doc_date_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        create_new_document() 
        
        text_title.delete(0, tk.END)
        text_title.insert(0, data.get('タイトル', ''))
        
        genre_var.set(data.get('ジャンル', GENRE_LIST[0]))
        
        text_signature.delete(0, tk.END)
        text_signature.insert(0, data.get('署名', ''))
        
        text_body.insert('1.0', data.get('本文', ''))
        
        date_part = current_doc_date_time.split(' ')[0] if current_doc_date_time else datetime.now().strftime('%Y-%m-%d')

        text_date.config(state=tk.NORMAL)
        text_date.delete(0, tk.END)
        text_date.insert(0, date_part)
        text_date.config(state=tk.DISABLED)
        
        update_confirmation_box(f"✅ ファイル '{os.path.basename(filepath)}' の内容をエディタにロードしました。編集後、[JSON保存]で上書き保存してください。", 'success')
        update_text_count()
        
    except Exception as e:
        update_confirmation_box(f"❌ エディタへのロードエラー: {e}", 'error')


def load_document_content(filepath):
    """単一の文書をプレビューします。"""
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        parsed_title = data.get('タイトル', 'N/A')
        parsed_genre = data.get('ジャンル', 'N/A')
        parsed_date = data.get('日付', 'N/A')
        parsed_body = data.get('本文', 'N/A')
        parsed_signature = data.get('署名', 'N/A')
        
        preview_content = format_document_preview(
            parsed_genre, parsed_title, parsed_date, parsed_body, parsed_signature
        )
        
        update_preview_text(preview_content, content_type='document', filepath=filepath)
        
        update_confirmation_box(f"✅ ファイル '{os.path.basename(filepath)}' を展開しました。", 'success')
        
    except Exception as e:
        update_confirmation_box(f"❌ プレビューエラー: {e}", 'error')


def load_document():
    filepath = filedialog.askopenfilename(
        defaultextension=".json",
        filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        title="文書JSONファイルを選択してください",
        initialdir=app_settings['default_load_path'] if app_settings['default_load_path'] else os.getcwd() 
    )
    if not filepath:
        update_confirmation_box("📂 ファイルの選択がキャンセルされました。", 'info')
        return

    load_document_content(filepath)


def load_folder(force_dialog=False):
    global current_folder_path, current_json_data, current_json_file_paths, active_genre_filter
    
    folderpath = current_folder_path
    
    if force_dialog or not folderpath or not os.path.isdir(folderpath):
        folderpath = filedialog.askdirectory(
            title="文書フォルダを選択してください",
            initialdir=app_settings['default_load_path'] if app_settings['default_load_path'] else os.getcwd()
        )
        if not folderpath:
            update_confirmation_box("📂 フォルダの選択がキャンセルされました。", 'info')
            return
        
    current_folder_path = folderpath
    save_config()

    current_json_data = []
    current_json_file_paths = []
    
    json_files = [f for f in os.listdir(folderpath) if f.endswith('.json')]
    
    for filename in json_files:
        filepath_full = os.path.join(folderpath, filename)
        try:
            with open(filepath_full, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            data['filename'] = filename
            current_json_data.append(data)
            current_json_file_paths.append(filepath_full)
            
        except json.JSONDecodeError:
            update_confirmation_box(f"❌ エラー: '{filename}' はJSON形式が不正です。", 'error')
        except Exception as e:
            update_confirmation_box(f"❌ エラー: '{filename}' の読み込みに失敗しました: {e}", 'error')

    active_genre_filter = "すべて"
    load_folder_view()
    update_confirmation_box(f"✅ フォルダ内容を読み込みました/更新しました。\nフォルダ: {os.path.basename(folderpath)}\nJSONファイル数: {len(current_json_data)}件", 'success')


def load_folder_view(*args):
    global preview_area_frame, current_folder_path, current_json_data, notebook, active_genre_filter, tab_list_frames, search_entry, sort_var
    
    for widget in preview_area_frame.winfo_children():
        widget.destroy()

    if not current_folder_path or not os.path.isdir(current_folder_path):
        default_label = tk.Label(preview_area_frame, text="📁 フォルダ読み込みボタンを押して、ドキュメントフォルダを選択してください。", 
                                bg=BG_COLOR, fg=FG_COLOR, font=FONT)
        default_label.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        return

    # 1. コントロールフレームを再構築
    control_frame = tk.Frame(preview_area_frame, bg='gray15', padx=10, pady=5)
    control_frame.pack(fill=tk.X)
    
    # --- コントロールの配置 ---
    tk.Label(control_frame, text="🔍 検索 (全文):", bg='gray15', fg=FG_COLOR, font=FONT).pack(side=tk.LEFT, padx=(0, 5))
    search_entry = tk.Entry(control_frame, width=30, **entry_style)
    search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
    search_entry.bind('<KeyRelease>', apply_filter_sort) 

    tk.Label(control_frame, text="ソート:", bg='gray15', fg=FG_COLOR, font=FONT).pack(side=tk.LEFT, padx=(10, 5))
    sort_options = ["日付 降順 (新→古)", "日付 昇順 (古→新)", "ジャンル別", "署名別", "タイトル別"]
    sort_menu = tk.OptionMenu(control_frame, sort_var, *sort_options, command=apply_filter_sort)
    sort_menu.config(**{'bg': 'gray30', 'fg': FG_COLOR, 'font': FONT, 'activebackground': 'green', 'activeforeground': 'white', 'relief': tk.RAISED, 'bd': 1})
    sort_menu.nametowidget(sort_menu.menuname).config(bg='gray15', fg='lime green', font=FONT, activebackground='darkgreen', activeforeground='white')
    sort_menu.pack(side=tk.LEFT, padx=(0, 5))

    # 2. タブ (ttk.Notebook) を再構築
    notebook = ttk.Notebook(preview_area_frame)
    notebook.pack(fill=tk.BOTH, expand=True)
    
    genre_counts = defaultdict(int)
    for data in current_json_data:
        genre_counts[data.get('ジャンル', 'その他')] += 1
    
    all_genres = ["すべて"] + sorted(genre_counts.keys())
    tab_list_frames.clear()

    # TabChangeイベントのハンドラ
    def on_tab_change(event):
        global active_genre_filter
        selected_tab_text = notebook.tab(notebook.select(), "text")
        match = re.match(r'(.+?)\s*\(\d+\)$', selected_tab_text)
        active_genre_filter = match.group(1) if match else "すべて"
        apply_filter_sort()

    notebook.bind('<<NotebookTabChanged>>', on_tab_change)

    # タブの生成とリスト構造の作成
    for genre in all_genres:
        count = genre_counts[genre] if genre != "すべて" else len(current_json_data)
        tab_text = f"{genre} ({count})"
        tab_frame = tk.Frame(notebook, bg='gray15')
        notebook.add(tab_frame, text=tab_text)

        list_structure_frame = create_scrollable_list_structure(tab_frame)
        tab_list_frames[genre] = list_structure_frame

        if genre == active_genre_filter: 
            notebook.select(tab_frame) 

    # リストの描画を実行
    apply_filter_sort()


def create_scrollable_list_structure(parent_frame):
    
    list_frame = tk.Frame(parent_frame, bg='gray15')
    list_frame.pack(fill=tk.BOTH, expand=True)
    
    canvas = tk.Canvas(list_frame, bg='gray15', borderwidth=0, highlightthickness=0)
    vscroll = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview, style="TLWR.Vertical.TScrollbar")
    
    vscroll.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)
    canvas.configure(yscrollcommand=vscroll.set)
    
    inner_frame = tk.Frame(canvas, bg='gray15')
    canvas_window = canvas.create_window((0, 0), window=inner_frame, anchor="nw") 
    
    def on_frame_configure(event):
        canvas.configure(scrollregion=canvas.bbox("all"))
        
    def on_canvas_resize(event):
        canvas.itemconfig(canvas_window, width=event.width)
    
    inner_frame.bind("<Configure>", on_frame_configure)
    canvas.bind('<Configure>', on_canvas_resize)
    
    return inner_frame


def apply_filter_sort(*args):
    global current_json_data, current_json_file_paths, search_entry, sort_var, active_genre_filter, tab_list_frames
    
    if not current_json_data:
        return

    inner_frame = tab_list_frames.get(active_genre_filter)
    if not inner_frame:
        return

    for widget in inner_frame.winfo_children():
        widget.destroy()

    search_term = search_entry.get().lower() if search_entry and search_entry.winfo_exists() else ""
    filtered_data_indices = []
    
    for i, data in enumerate(current_json_data):
        searchable_text = f"{data.get('タイトル', '')} {data.get('ジャンル', '')} {data.get('署名', '')} {data.get('filename', '')} {data.get('本文', '')}".lower()
        genre_match = (active_genre_filter == "すべて" or data.get('ジャンル') == active_genre_filter)
        
        if search_term in searchable_text and genre_match:
            filtered_data_indices.append(i)
            
    sort_key = sort_var.get() if sort_var else "日付 降順 (新→古)"
    
    def get_sort_key(index):
        data = current_json_data[index]
        if sort_key.startswith("日付"):
            return data.get('日付', '0000-00-00 00:00:00')
        elif sort_key == "ジャンル別":
            return data.get('ジャンル', '')
        elif sort_key == "署名別":
            return data.get('署名', '')
        elif sort_key == "タイトル別":
            return data.get('タイトル', '')
        return 0

    is_reverse = sort_key == "日付 降順 (新→古)"
    try:
        filtered_data_indices.sort(key=get_sort_key, reverse=is_reverse)
    except Exception as e:
        update_confirmation_box(f"❌ ソートエラー: {e}", 'error')

    folderpath = os.path.basename(current_folder_path)
    header_label = tk.Label(inner_frame, 
                            text=f"--- フォルダ内容 ( {folderpath} ) ---\n表示数: {len(filtered_data_indices)}件 / 全{len(current_json_data)}件 ({active_genre_filter}タブ)", 
                            bg='gray15', fg='yellow', font=FONT)
    header_label.pack(pady=(10, 5), padx=10, fill=tk.X)
    
    button_style = _get_button_style('gray30')

    for i, data_index in enumerate(filtered_data_indices, 1):
        data = current_json_data[data_index]
        filepath_full = current_json_file_paths[data_index]
        
        display_name = f"[{data.get('ジャンル', 'N/A')}] {data.get('タイトル', 'N/A')} (by {data.get('署名', 'N/A')}) - {data.get('日付', 'N/A').split(' ')[0]}"
        
        button = tk.Button(inner_frame, text=f"[{i:02d}] {display_name}", 
                           command=lambda fp=filepath_full: load_document_content(fp), 
                           **button_style)
        button.pack(pady=3, padx=10, fill=tk.X)
    
    canvas = inner_frame.master 
    canvas.configure(scrollregion=canvas.bbox("all"))
    
    if search_entry and search_entry.get() and search_entry.winfo_exists():
        update_confirmation_box(f"✅ フィルタとソートを適用しました。\n表示数: {len(filtered_data_indices)}件 ({active_genre_filter}タブ)", 'info')


def save_document():
    """現在の入力内容をJSONファイルとして保存します。編集モードの場合は元のタイムスタンプを維持して上書きします。"""
    global title_history, signature_history, current_editing_filepath, current_doc_date_time
    
    if not validate_input():
        update_confirmation_box("❌ エラー: 入力内容に問題があります。保存を中止しました。", 'error')
        return
        
    genre = genre_var.get().strip()
    title = text_title.get().strip() 
    signature = text_signature.get().strip()
    body = text_body.get('1.0', tk.END).strip()
    
    # 自動日付挿入機能 
    today_date_str = datetime.now().strftime('%Y/%m/%d')
    body = body.replace('[today]', today_date_str)
    
    # 編集モードの場合、元のタイムスタンプを維持 
    if current_editing_filepath and current_doc_date_time:
        date_with_time = current_doc_date_time
        date_for_filename = datetime.strptime(date_with_time, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d_%H-%M-%S')
        initial_file_name = os.path.basename(current_editing_filepath)
    else:
        # 新規作成/別名保存の場合
        current_datetime_obj = datetime.now()
        date_with_time = current_datetime_obj.strftime('%Y-%m-%d %H:%M:%S')
        date_for_filename = current_datetime_obj.strftime('%Y-%m-%d_%H-%M-%S')
        
        safe_genre = re.sub(INVALID_FILENAME_CHARS, '_', genre)
        safe_signature = re.sub(INVALID_FILENAME_CHARS, '_', signature)
        initial_file_name = f"{safe_genre}_{safe_signature}_{date_for_filename}.json"
    
    if not title or not signature:
        update_confirmation_box("⚠️ 警告: タイトルと署名は必須です。保存を中止しました。", 'warning')
        return

    data_to_save = {
        "ジャンル": genre,
        "タイトル": title, 
        "日付": date_with_time, 
        "本文": body,
        "署名": signature
    }
    
    default_path = os.path.dirname(current_editing_filepath) if current_editing_filepath else app_settings['default_save_path']
    
    filepath = filedialog.asksaveasfilename(
        defaultextension=".json",
        filetypes=[("JSON files", "*.json")],
        title="ファイルを保存",
        initialfile=initial_file_name,
        initialdir=default_path if default_path else os.getcwd()
    )
    
    if not filepath:
        update_confirmation_box("📂 ファイルの保存がキャンセルされました。", 'info')
        return

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=4)
            
        if title:
            title_history.insert(0, title) 
        if signature:
            signature_history.insert(0, signature)
        
        save_config() 
        
        text_title.config(values=title_history)
        text_signature.config(values=signature_history)
        
        current_editing_filepath = filepath
        current_doc_date_time = date_with_time
        
        update_confirmation_box(f"✅ 文書を正常にJSON形式で保存/上書きしました。\nファイル名: {os.path.basename(filepath)}", 'success')
        
    except Exception as e:
        update_confirmation_box(f"❌ エラー: ファイルの保存に失敗しました。\nエラー内容: {e}", 'error')


def export_document():
    """現在の文書の内容をTXTファイルとしてエクスポートします。"""
    
    title = text_title.get().strip()
    genre = genre_var.get().strip()
    body = text_body.get('1.0', tk.END).strip()
    signature = text_signature.get().strip()
    date = datetime.now().strftime('%Y-%m-%d')
    
    if not title or not body:
        update_confirmation_box("⚠️ エクスポートエラー: タイトルと本文を入力してください。", 'warning')
        return
        
    export_content = (
        f"タイトル: {title}\n"
        f"ジャンル: {genre}\n"
        f"日付: {date}\n"
        f"署名: {signature}\n"
        f"--- 本文 ---\n"
        f"{body}\n"
        f"------------\n"
    )
    
    filepath = filedialog.asksaveasfilename(
        title="文書をエクスポート",
        defaultextension=".txt",
        initialfile=f"{title}_{date}",
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
    )
    
    if not filepath:
        update_confirmation_box("📂 エクスポートがキャンセルされました。", 'info')
        return

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(export_content)
        update_confirmation_box(f"✅ TXTファイルとしてエクスポートしました。\nファイル: {os.path.basename(filepath)}", 'success')

    except Exception as e:
        update_confirmation_box(f"❌ エクスポートエラー: {e}", 'error')


def open_settings_window():
    settings_window = tk.Toplevel(text_title.winfo_toplevel())
    settings_window.title("TLWR 設定")
    settings_window.geometry("600x450")
    settings_window.configure(bg=BG_COLOR)
    
    tk.Label(settings_window, text="--- フォルダ / 設定管理 ---", bg=BG_COLOR, fg='yellow', font=(FONT_NAME, FONT_SIZE + 2, 'bold')).pack(pady=10)
    
    def select_path(key):
        path = filedialog.askdirectory(title=f"{key} フォルダを選択")
        if path:
            app_settings[key] = path
            path_vars[key].set(path)

    def save_and_close():
        save_config()
        messagebox.showinfo("設定完了", "設定を保存しました。スプラッシュスクリーンの変更は再起動後に適用されます。", parent=settings_window)
        settings_window.destroy()

    path_vars = {}
    
    load_frame = tk.Frame(settings_window, bg=BG_COLOR)
    load_frame.pack(fill=tk.X, padx=20, pady=5)
    tk.Label(load_frame, text="既定の読み込みフォルダ:", bg=BG_COLOR, fg=FG_COLOR).pack(side=tk.LEFT, anchor='w')
    path_vars['default_load_path'] = tk.StringVar(value=app_settings['default_load_path'] if app_settings['default_load_path'] else "未設定")
    tk.Entry(load_frame, textvariable=path_vars['default_load_path'], width=50, state='readonly', bg='gray15', fg=FG_COLOR).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
    tk.Button(load_frame, text="選択", command=lambda: select_path('default_load_path'), bg='gray30', fg=FG_COLOR).pack(side=tk.RIGHT)

    save_frame = tk.Frame(settings_window, bg=BG_COLOR)
    save_frame.pack(fill=tk.X, padx=20, pady=5)
    tk.Label(save_frame, text="既定の保存フォルダ:", bg=BG_COLOR, fg=FG_COLOR).pack(side=tk.LEFT, anchor='w')
    path_vars['default_save_path'] = tk.StringVar(value=app_settings['default_save_path'] if app_settings['default_save_path'] else "未設定")
    tk.Entry(save_frame, textvariable=path_vars['default_save_path'], width=50, state='readonly', bg='gray15', fg=FG_COLOR).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
    tk.Button(save_frame, text="選択", command=lambda: select_path('default_save_path'), bg='gray30', fg=FG_COLOR).pack(side=tk.RIGHT)

    tk.Label(settings_window, text="--- アプリケーション設定 ---", bg=BG_COLOR, fg='yellow', font=FONT).pack(pady=(20, 5))

    splash_frame = tk.Frame(settings_window, bg=BG_COLOR)
    splash_frame.pack(fill=tk.X, padx=20, pady=5)
    disable_splash_var = tk.BooleanVar(value=app_settings['disable_splash_screen'])
    def toggle_splash():
        app_settings['disable_splash_screen'] = disable_splash_var.get()
    tk.Checkbutton(splash_frame, text="起動時のスプラッシュスクリーンを無効化する", variable=disable_splash_var, command=toggle_splash, bg=BG_COLOR, fg=FG_COLOR, selectcolor='gray15').pack(side=tk.LEFT, anchor='w')

    config_frame = tk.Frame(settings_window, bg=BG_COLOR)
    config_frame.pack(fill=tk.X, padx=20, pady=5)
    use_config_var = tk.BooleanVar(value=app_settings['use_config_file'])
    def toggle_config():
        app_settings['use_config_file'] = use_config_var.get()
    tk.Checkbutton(config_frame, text="設定ファイル (config) を利用する", variable=use_config_var, command=toggle_config, bg=BG_COLOR, fg=FG_COLOR, selectcolor='gray15').pack(side=tk.LEFT, anchor='w')

    def select_config_file():
        filepath = filedialog.askopenfilename(title="設定ファイルを選択", defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if filepath:
            app_settings['last_selected_config'] = filepath 
            config_file_var.set(os.path.basename(filepath))

    config_select_frame = tk.Frame(settings_window, bg=BG_COLOR)
    config_select_frame.pack(fill=tk.X, padx=20, pady=5)
    tk.Label(config_select_frame, text="使用するConfigファイル:", bg=BG_COLOR, fg=FG_COLOR).pack(side=tk.LEFT, anchor='w')
    
    display_config_name = os.path.basename(app_settings['last_selected_config']) if app_settings['last_selected_config'] else CONFIG_FILE
    config_file_var = tk.StringVar(value=display_config_name)
    
    tk.Entry(config_select_frame, textvariable=config_file_var, width=30, state='readonly', bg='gray15', fg=FG_COLOR).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
    tk.Button(config_select_frame, text="選択", command=select_config_file, bg='gray30', fg=FG_COLOR).pack(side=tk.RIGHT)
    
    tk.Button(settings_window, text="設定を保存して閉じる", command=save_and_close, **_get_button_style('darkgreen')).pack(pady=20, padx=20, fill=tk.X)


# --- GUIのセットアップ (左右分割ビュー) ---

def setup_gui():
    global text_title, text_date, text_body, text_signature, genre_var, confirm_text, preview_area_frame, sort_var, count_label
    
    root = tk.Tk()
    root.title("Text&Letter Writer&Reader") 
    root.configure(bg=BG_COLOR)
    
    load_config()

    label_style = {'bg': BG_COLOR, 'fg': FG_COLOR, 'font': FONT}
    global entry_style
    entry_style = {'bg': 'gray15', 'fg': FG_COLOR, 'insertbackground': FG_COLOR, 'font': FONT, 'relief': tk.SOLID, 'bd': 1}
    
    style = ttk.Style(root)
    style.theme_use('clam')
    
    # TComboboxのスタイル定義を再確認
    style.configure("TCombobox", 
                    fieldbackground='gray15', foreground=FG_COLOR, selectbackground='gray15', selectforeground=FG_COLOR,
                    background='gray30', insertbackground=FG_COLOR)
    style.map("TCombobox",
              fieldbackground=[('readonly', 'gray15')],
              foreground=[('readonly', FG_COLOR)]
              )
    style.configure("TLWR.Vertical.TScrollbar", background='gray30', troughcolor='gray15', bordercolor='gray30', arrowcolor=FG_COLOR)
    style.map("TLWR.Vertical.TScrollbar", background=[('active', 'gray40')], relief=[('pressed', 'sunken'), ('!active', 'flat')])
    
    style.configure('TNotebook', background=BG_COLOR, borderwidth=0)
    style.map('TNotebook.Tab', background=[('selected', 'gray30'), ('!selected', 'gray25')], 
                               foreground=[('selected', FG_COLOR), ('!selected', 'gray')])


    window_width = 1200 
    window_height = 800
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x_cordinate = (screen_width // 2) - (window_width // 2)
    y_cordinate = (screen_height // 2) - (window_height // 2)
    root.geometry(f'{window_width}x{window_height}+{x_cordinate}+{y_cordinate}')

    button_style = {'bg': 'darkgreen', 'fg': FG_COLOR, 'font': (FONT_NAME, FONT_SIZE, 'bold'), 'activebackground': 'green', 'activeforeground': 'white', 'relief': tk.RAISED, 'bd': 2}
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
    
    # 1. アクションボタン群 
    button_frame = tk.Frame(left_frame, bg=BG_COLOR)
    button_frame.pack(pady=(0, 15), fill=tk.X)
    
    tk.Button(button_frame, text="📄 新規作成", command=create_new_document, **button_style).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
    tk.Button(button_frame, text="💾 JSON保存", command=save_document, **button_style).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5, 5))
    tk.Button(button_frame, text="📤 エクスポート", command=export_document, **_get_button_style('darkred')).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5, 5))
    tk.Button(button_frame, text="⚙️ 設定", command=open_settings_window, **_get_button_style('gray30')).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5, 0))


    # 2. メタデータ入力
    tk.Label(left_frame, text="Title:", **label_style).pack(pady=(5, 2), anchor='w') 
    text_title = ttk.Combobox(left_frame, width=80, values=title_history, font=FONT, style="TCombobox")
    text_title.pack(fill=tk.X)
    text_title.bind('<KeyRelease>', validate_input)
    text_title.set('')

    tk.Label(left_frame, text="Genre Date:", **label_style).pack(pady=(10, 2), anchor='w') 
    date_genre_frame = tk.Frame(left_frame, bg=BG_COLOR)
    date_genre_frame.pack(fill=tk.X)
    
    template_button = tk.Button(date_genre_frame, text="📄 テンプレート挿入", command=apply_template, 
                                **_get_button_style('gray30'))
    template_button.pack(side=tk.LEFT, padx=(0, 10))
    
    text_date = tk.Entry(date_genre_frame, width=15, **entry_style)
    text_date.insert(0, datetime.now().strftime('%Y-%m-%d'))
    text_date.config(state=tk.DISABLED) 
    text_date.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
    
    genre_var = tk.StringVar(root)
    genre_var.set(GENRE_LIST[0]) 
    option_menu = tk.OptionMenu(date_genre_frame, genre_var, *GENRE_LIST) 
    option_menu.config(**option_menu_style)
    menu = root.nametowidget(option_menu.menuname)
    menu.config(bg='gray15', fg='lime green', font=FONT, activebackground='darkgreen', activeforeground='white')
    option_menu.pack(side=tk.RIGHT)
    
    tk.Label(left_frame, text="text (本文):", **label_style).pack(pady=(10, 2), anchor='w') 
    
    text_body_frame = tk.Frame(left_frame, bg=BG_COLOR)
    text_body_frame.pack(pady=(0, 10), fill=tk.BOTH, expand=True)
    
    # --- Textウィジェットとスクロールバーを格納する内部フレーム ---
    text_scroll_frame = tk.Frame(text_body_frame, bg=BG_COLOR)
    text_scroll_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    text_body = tk.Text(text_scroll_frame, wrap=tk.WORD, height=15, **text_area_style)
    
    vscroll_body = ttk.Scrollbar(text_scroll_frame, orient=tk.VERTICAL, command=text_body.yview, style="TLWR.Vertical.TScrollbar")
    vscroll_body.pack(side=tk.RIGHT, fill=tk.Y)
    text_body.configure(yscrollcommand=vscroll_body.set)

    text_body.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    # 🌟 修正: 句読点変換を <Key> イベントでバインド 🌟
    text_body.bind('<Key>', convert_punctuation)
    
    # 文字数カウントとバリデーションは <KeyRelease> イベントでバインド
    text_body.bind('<KeyRelease>', update_text_count)
    text_body.bind('<KeyRelease>', validate_input, add='+')
    
    # 🌟 カウンターラベルを Text/Scrollbarの下部に独立して配置 🌟
    count_label = tk.Label(text_body_frame, text="文字数: 0 | 行数: 1", bg=BG_COLOR, fg='gray', font=(FONT_NAME, FONT_SIZE - 2))
    count_label.pack(side=tk.BOTTOM, fill=tk.X, pady=(2, 0))


    tk.Label(left_frame, text="Name (署名):", **label_style).pack(pady=(5, 2), anchor='w') 
    text_signature = ttk.Combobox(left_frame, width=80, values=signature_history, font=FONT, style="TCombobox")
    text_signature.pack(fill=tk.X)
    text_signature.bind('<KeyRelease>', validate_input)
    text_signature.set('')

    # 3. 確認ボックス 
    tk.Label(left_frame, text="--- 状況 / メッセージ ---", **label_style).pack(pady=(10, 0), anchor='w')
    
    confirm_text_frame = tk.Frame(left_frame, bg=BG_COLOR)
    confirm_text_frame.pack(pady=5, fill=tk.X)

    confirm_text = tk.Text(confirm_text_frame, wrap=tk.WORD, height=3, **text_area_style, state=tk.DISABLED)
    vscroll_confirm = ttk.Scrollbar(confirm_text_frame, orient=tk.VERTICAL, command=confirm_text.yview, style="TLWR.Vertical.TScrollbar")
    vscroll_confirm.pack(side=tk.RIGHT, fill=tk.Y)
    confirm_text.configure(yscrollcommand=vscroll_confirm.set)
    confirm_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    confirm_text.tag_config('error', foreground='red')
    confirm_text.tag_config('info', foreground='gray')
    confirm_text.tag_config('warning', foreground='yellow')
    confirm_text.tag_config('success', foreground=FG_COLOR, font=(FONT_NAME, FONT_SIZE, 'bold'))
    
    update_confirmation_box("✅ アプリケーションを起動しました。新規文書を作成するか、フォルダを読み込んでください。", 'success')


    # --- B. 右側フレーム (閲覧/ファイル読み込み専用) ---
    right_frame = tk.Frame(paned_window, bg=BG_COLOR, padx=15, pady=15)
    paned_window.add(right_frame, weight=1) 

    # 1. アクションボタン群
    right_button_frame = tk.Frame(right_frame, bg=BG_COLOR)
    right_button_frame.pack(pady=(0, 15), fill=tk.X)
    
    tk.Button(right_button_frame, text="📂 File Reader", command=load_document, **button_style).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
    tk.Button(right_button_frame, text="📁 フォルダ選択", command=lambda: load_folder(force_dialog=True), **button_style).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5, 5))
    tk.Button(right_button_frame, text="🔁 再読み込み", command=lambda: load_folder(force_dialog=False), **_get_button_style('gray30')).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5, 0))
    
    tk.Label(right_frame, text="➡️ 閲覧 / プレビュー画面", font=(FONT_NAME, FONT_SIZE + 4, 'bold'), fg='light green', bg=BG_COLOR).pack(pady=10)
    
    # 2. 閲覧エリア (動的にウィジェットを格納するためのフレーム)
    preview_area_frame = tk.Frame(right_frame, bg=BG_COLOR)
    preview_area_frame.pack(pady=5, fill=tk.BOTH, expand=True)
    
    sort_var = tk.StringVar(root)
    sort_var.set("日付 降順 (新→古)")

    update_text_count() 
    
    if current_folder_path and os.path.isdir(current_folder_path):
        load_folder(force_dialog=False)
    else:
        load_folder_view()
    
    root.mainloop()

if __name__ == "__main__":
    
    def setup_main_gui():
        setup_gui()
        
    def show_splash_screen(setup_main_gui_func):
        
        load_config()
        if app_settings['disable_splash_screen']:
            setup_main_gui_func()
            return

        splash = tk.Tk()
        splash.overrideredirect(True) 
        splash.attributes('-topmost', True) 
        splash.config(bg=BG_COLOR) 

        splash_width = 700
        splash_height = 400
        screen_width = splash.winfo_screenwidth()
        screen_height = splash.winfo_screenheight()
        x = (screen_width // 2) - (splash_width // 2)
        y = (screen_height // 2) - (splash_height // 2)
        splash.geometry(f'{splash_width}x{splash_height}+{x}+{y}')

        logo_frame = tk.Frame(splash, bg=BG_COLOR)
        logo_frame.pack(expand=True, padx=40, pady=40)

        tk.Label(logo_frame, text="✍️ 📂", 
                 font=("Segoe UI Emoji", 48, 'bold'), fg=FG_COLOR, bg=BG_COLOR).pack(side=tk.LEFT, padx=(0, 30))

        title_frame = tk.Frame(logo_frame, bg=BG_COLOR)
        title_frame.pack(side=tk.LEFT, anchor='center')

        tk.Label(title_frame, text="Text & Letter", 
                 font=(FONT_NAME, FONT_SIZE + 20, 'bold'), fg=FG_COLOR, bg=BG_COLOR).pack(anchor='w')
        tk.Label(title_frame, text="Writer & Reader", 
                 font=(FONT_NAME, FONT_SIZE + 15, 'bold'), fg=FG_COLOR, bg=BG_COLOR).pack(anchor='w')
        
        tk.Label(splash, text="TLWR Version 3.0[Mikado] (2025/11/21)", 
                 font=(FONT_NAME, FONT_SIZE + 2, 'bold'), fg=FG_COLOR, bg=BG_COLOR).pack(side=tk.BOTTOM, anchor='se', padx=20, pady=10)

        def start_main_app():
            splash.destroy()      
            setup_main_gui_func() 

        splash.after(3000, start_main_app) 

        splash.mainloop()
        
    show_splash_screen(setup_main_gui)
