import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import sqlite3
import json
import os
import sys
import time

# ==========================================
#  設定・テーマ定義
# ==========================================
def get_app_path():
    if getattr(sys, 'frozen', False):
        # exe化されている場合、exeファイルの場所を取得
        return os.path.dirname(sys.executable)
    else:
        # スクリプト実行の場合、ファイルの場所を取得
        return os.path.dirname(os.path.abspath(__file__))

# DBファイルのパスを絶対パスで指定
DB_FILE = os.path.join(get_app_path(), "dictionary.db")

THEMES = {
    "Dark": {
        "bg": "#000000", "fg": "#00FF00", "fg_dim": "#008800",
        "input_bg": "#111111", "input_fg": "#FFFFFF",
        "accent": "#006600", "accent_hover": "#009900",
        "list_bg": "#080808", "list_fg": "#00FF00",
        "select_bg": "#006600", "select_fg": "#FFFFFF",
        "log_fg_info": "#00FF00", "log_fg_err": "#FF0000",
        "btn_bg": "#333333", "btn_fg": "#FFFFFF"
    },
    "Light": {
        "bg": "#F0F0F0", "fg": "#000000", "fg_dim": "#555555",
        "input_bg": "#FFFFFF", "input_fg": "#000000",
        "accent": "#4CAF50", "accent_hover": "#45a049",
        "list_bg": "#FFFFFF", "list_fg": "#000000",
        "select_bg": "#4CAF50", "select_fg": "#FFFFFF",
        "log_fg_info": "#000000", "log_fg_err": "#FF0000",
        "btn_bg": "#DDDDDD", "btn_fg": "#000000"
    }
}

PART_OF_SPEECH_LIST = [
    "N(名詞)", "V(動詞)", "Adj(形容詞)", "Adv(副詞)", 
    "Conj(接続詞)", "Prep(前置詞)", "Pro(代名詞)", 
    "Det(限定詞)", "Aux(助動詞)", "Part(助詞)", "Num(数詞)", "Other"
]

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# ==========================================
#  データベース管理クラス
# ==========================================
class DatabaseManager:
    def __init__(self, db_file):
        self.db_file = db_file
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_file)

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS dictionary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    term TEXT UNIQUE,
                    pronunciation TEXT,
                    pos TEXT,
                    meaning TEXT,
                    example TEXT,
                    sort_order INTEGER
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            conn.commit()

    def get_all_words(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM dictionary ORDER BY sort_order ASC")
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def upsert_word(self, data):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM dictionary WHERE term = ?", (data['term'],))
            exists = cursor.fetchone()
            if exists:
                cursor.execute("""
                    UPDATE dictionary SET pronunciation=?, pos=?, meaning=?, example=? WHERE term=?
                """, (data['pronunciation'], data['pos'], data['meaning'], data['example'], data['term']))
                return "updated"
            else:
                cursor.execute("SELECT MAX(sort_order) FROM dictionary")
                max_order = cursor.fetchone()[0]
                new_order = 1 if max_order is None else max_order + 1
                cursor.execute("""
                    INSERT INTO dictionary (term, pronunciation, pos, meaning, example, sort_order)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (data['term'], data['pronunciation'], data['pos'], data['meaning'], data['example'], new_order))
                return "created"

    def delete_word(self, term):
        with self.get_connection() as conn:
            conn.execute("DELETE FROM dictionary WHERE term = ?", (term,))

    def update_order(self, term1, order1, term2, order2):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE dictionary SET sort_order = ? WHERE term = ?", (order1, term1))
            cursor.execute("UPDATE dictionary SET sort_order = ? WHERE term = ?", (order2, term2))
            conn.commit()

    def get_setting(self, key, default=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            res = cursor.fetchone()
            return res[0] if res else default

    def set_setting(self, key, value):
        with self.get_connection() as conn:
            conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))

# ==========================================
#  メインアプリケーション
# ==========================================
class ReDicSearcherApp:
    def __init__(self, root):
        self.root = root
        self.root.geometry("950x750")
        self.root.withdraw() 

        self.db = DatabaseManager(DB_FILE)
        
        # 設定ロード
        self.current_theme_name = self.db.get_setting("theme", "Dark")
        self.splash_style = self.db.get_setting("splash_style", "Classic") # Default to Classic (v1.0 style)
        
        self.colors = THEMES[self.current_theme_name]
        self.search_mode = tk.StringVar(value="contains")
        self.data_cache = []
        self.widgets = {}
        
        self.apply_theme_to_root()
        self.show_splash()

    def apply_theme_to_root(self):
        self.root.configure(bg=self.colors["bg"])
        self.root.title(f"Re.DicSearcher v2.2 [{self.current_theme_name}]")

    # ==========================================
    #  スプラッシュスクリーン分岐
    # ==========================================
    def show_splash(self):
        if self.splash_style == "Modern":
            self.show_splash_modern()
        else:
            self.show_splash_classic()

    def show_splash_modern(self):
        """v2.0風: 画像中心の静かな起動画面"""
        splash = tk.Toplevel(self.root)
        splash.overrideredirect(True)
        splash.attributes('-topmost', True)
        w, h = 500, 300
        x = (self.root.winfo_screenwidth()//2) - (w//2)
        y = (self.root.winfo_screenheight()//2) - (h//2)
        splash.geometry(f"{w}x{h}+{x}+{y}")
        splash.configure(bg=self.colors["bg"])

        try:
            from PIL import Image, ImageTk
            img_path = resource_path("logo.png")
            if os.path.exists(img_path):
                raw = Image.open(img_path)
                raw.thumbnail((100, 100))
                img = ImageTk.PhotoImage(raw)
                lbl = tk.Label(splash, image=img, bg=self.colors["bg"])
                lbl.image = img
                lbl.pack(pady=20)
            else:
                raise Exception
        except:
            tk.Label(splash, text="Re.Dic", font=("Consolas", 40, "bold"), 
                     bg=self.colors["bg"], fg=self.colors["fg"]).pack(pady=20)

        tk.Label(splash, text="LOADING SYSTEM...", font=("Consolas", 10), 
                 bg=self.colors["bg"], fg=self.colors["fg"]).pack(side=tk.BOTTOM, pady=20)
        
        splash.after(1500, lambda: self.startup_sequence(splash))

    def show_splash_classic(self):
        """v1.0風: ハッカー風アニメーション付き起動画面"""
        splash = tk.Toplevel(self.root)
        splash.overrideredirect(True)
        splash.attributes('-topmost', True)
        w, h = 500, 300
        x = (self.root.winfo_screenwidth()//2) - (w//2)
        y = (self.root.winfo_screenheight()//2) - (h//2)
        splash.geometry(f"{w}x{h}+{x}+{y}")
        splash.configure(bg=self.colors["bg"])

        # 枠線演出
        tk.Frame(splash, bg=self.colors["fg"], width=w, height=2).pack(side=tk.TOP)
        tk.Frame(splash, bg=self.colors["fg"], width=w, height=2).pack(side=tk.BOTTOM)
        tk.Frame(splash, bg=self.colors["fg"], width=2, height=h).place(x=0, y=0)
        tk.Frame(splash, bg=self.colors["fg"], width=2, height=h).place(x=w-2, y=0)

        content = tk.Frame(splash, bg=self.colors["bg"])
        content.pack(expand=True)
        
        tk.Label(content, text="[DICTIONARY SYSTEM]", font=("Consolas", 16, "bold"), 
                 bg=self.colors["bg"], fg=self.colors["fg"]).pack(pady=10)
        tk.Label(content, text="INITIALIZING...", font=("Consolas", 12, "bold"), 
                 bg=self.colors["bg"], fg=self.colors["fg"]).pack(pady=5)
        
        loading_lbl = tk.Label(content, text="", font=("Consolas", 12), bg=self.colors["bg"], fg=self.colors["fg"])
        loading_lbl.pack(pady=10)

        def update_loading(count=0):
            chars = ["|", "/", "-", "\\"]
            loading_lbl.config(text=f"LOADING MODULES {chars[count % 4]}")
            if count < 18: 
                splash.after(80, update_loading, count+1)
            else:
                self.startup_sequence(splash)
        
        update_loading()

    def startup_sequence(self, splash):
        self.data_cache = self.db.get_all_words()
        self.setup_ui()
        splash.destroy()
        self.root.deiconify()
        self.log(f"System ready. {len(self.data_cache)} words loaded.", "success")

    # ==========================================
    #  UIセットアップ
    # ==========================================
    def setup_ui(self):
        self.widgets = {}

        # --- ヘッダー ---
        header = tk.Frame(self.root, bg=self.colors["bg"], pady=10, padx=10)
        header.pack(fill=tk.X)
        self.widgets["header_frame"] = header

        # ボタン群
        self.btn_import = tk.Button(header, text="📂 IMPORT", command=self.import_json_dialog,
                                    relief="flat", padx=10)
        self.btn_import.pack(side=tk.LEFT, padx=(0, 5))
        self.widgets["btn_import"] = self.btn_import

        # ★ 設定ボタン (旧THEMEボタンを機能強化) ★
        self.btn_config = tk.Button(header, text="⚙ CONFIG", command=self.open_config_dialog,
                                    relief="flat", padx=10)
        self.btn_config.pack(side=tk.LEFT)
        self.widgets["btn_config"] = self.btn_config

        self.btn_mode = tk.Button(header, text="MODE: READ", command=self.toggle_mode,
                                  relief="flat", padx=15, font=("Consolas", 11, "bold"))
        self.btn_mode.pack(side=tk.RIGHT)
        self.widgets["btn_mode"] = self.btn_mode

        # --- コンテンツエリア ---
        self.content_frame = tk.Frame(self.root, bg=self.colors["bg"])
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.widgets["content_frame"] = self.content_frame

        self.frame_read = tk.Frame(self.content_frame, bg=self.colors["bg"])
        self.setup_read_mode()
        
        self.frame_write = tk.Frame(self.content_frame, bg=self.colors["bg"])
        self.setup_write_mode()

        self.current_mode = "read"
        self.frame_read.pack(fill=tk.BOTH, expand=True)

        # --- ログエリア ---
        log_frame = tk.Frame(self.root, bg=self.colors["bg"], padx=10, pady=10)
        log_frame.pack(fill=tk.X, side=tk.BOTTOM)
        self.widgets["log_frame"] = log_frame

        self.lbl_log_title = tk.Label(log_frame, text="--- SYSTEM LOG ---", font=("Consolas", 9))
        self.lbl_log_title.pack(anchor="w")
        self.widgets["lbl_log_title"] = self.lbl_log_title

        self.log_text = tk.Text(log_frame, height=4, font=("Consolas", 10), state="disabled", relief="solid", bd=1)
        self.log_text.pack(fill=tk.X)
        self.widgets["log_text"] = self.log_text

        self.apply_theme_to_widgets()
        self.refresh_list()

    def setup_read_mode(self):
        # (v2.1と同様の実装)
        self.widgets["frame_read"] = self.frame_read
        
        search_frame = tk.Frame(self.frame_read, bg=self.colors["bg"], pady=5)
        search_frame.pack(fill=tk.X)
        self.widgets["search_frame"] = search_frame

        lbl_search = tk.Label(search_frame, text="SEARCH >", font=("Consolas", 11, "bold"))
        lbl_search.pack(side=tk.LEFT)
        self.widgets["lbl_search"] = lbl_search

        self.entry_search = tk.Entry(search_frame, font=("Consolas", 11), relief="flat")
        self.entry_search.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, ipady=3)
        self.entry_search.bind('<KeyRelease>', self.on_search)
        self.widgets["entry_search"] = self.entry_search

        opt_frame = tk.Frame(search_frame, bg=self.colors["bg"])
        opt_frame.pack(side=tk.LEFT)
        self.widgets["opt_frame"] = opt_frame
        
        self.radios = []
        for text, mode in [("In", "contains"), ("Start", "startswith"), ("End", "endswith")]:
            rb = tk.Radiobutton(opt_frame, text=text, variable=self.search_mode, value=mode,
                                command=self.on_search, font=("Consolas", 9),
                                selectcolor=self.colors["bg"])
            rb.pack(side=tk.LEFT)
            self.radios.append(rb)

        paned = tk.PanedWindow(self.frame_read, orient=tk.HORIZONTAL, bg=self.colors["bg"], sashwidth=4)
        paned.pack(fill=tk.BOTH, expand=True, pady=5)
        self.widgets["paned"] = paned

        left_group = tk.Frame(paned, bg=self.colors["bg"])
        paned.add(left_group, minsize=280)
        self.widgets["left_group"] = left_group

        order_frame = tk.Frame(left_group, bg=self.colors["bg"])
        order_frame.pack(side=tk.LEFT, fill=tk.Y)
        self.widgets["order_frame"] = order_frame
        
        self.btn_up = tk.Button(order_frame, text="▲", command=self.move_up, relief="flat", width=2)
        self.btn_up.pack(side=tk.TOP, pady=2)
        self.btn_down = tk.Button(order_frame, text="▼", command=self.move_down, relief="flat", width=2)
        self.btn_down.pack(side=tk.TOP, pady=2)
        self.widgets["btn_up"] = self.btn_up
        self.widgets["btn_down"] = self.btn_down

        self.listbox = tk.Listbox(left_group, font=("Consolas", 11), borderwidth=1, relief="solid")
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.listbox.bind('<<ListboxSelect>>', self.show_detail)
        self.widgets["listbox"] = self.listbox

        sb = tk.Scrollbar(left_group, orient=tk.VERTICAL, command=self.listbox.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=sb.set)

        detail_frame = tk.Frame(paned, bg=self.colors["bg"], padx=15)
        paned.add(detail_frame, minsize=400)
        self.widgets["detail_frame"] = detail_frame

        self.lbl_detail_term = tk.Label(detail_frame, text="", font=("Consolas", 20, "bold"), anchor="w")
        self.lbl_detail_term.pack(fill=tk.X, pady=(0, 10))
        self.widgets["lbl_detail_term"] = self.lbl_detail_term

        self.detail_text = tk.Text(detail_frame, font=("Consolas", 11), height=15, state="disabled", relief="flat", wrap="word")
        self.detail_text.pack(fill=tk.BOTH, expand=True)
        self.widgets["detail_text"] = self.detail_text

    def setup_write_mode(self):
        self.widgets["frame_write"] = self.frame_write
        self.entry_labels = []
        self.entries = {}
        
        lbl_title = tk.Label(self.frame_write, text="EDITOR / REGISTRATION", font=("Consolas", 14, "bold"), anchor="w")
        lbl_title.pack(pady=(0, 15))
        self.widgets["lbl_write_title"] = lbl_title

        def create_row(label, key):
            lbl = tk.Label(self.frame_write, text=f"■ {label}", font=("Consolas", 10, "bold"), anchor="w")
            lbl.pack(anchor="w")
            self.entry_labels.append(lbl)
            ent = tk.Entry(self.frame_write, font=("Consolas", 11), relief="flat")
            ent.pack(fill=tk.X, pady=(0, 10), ipady=5)
            self.entries[key] = ent
            self.widgets[f"entry_{key}"] = ent

        create_row("単語 (Term)", "term")
        create_row("発音 (Pronunciation)", "pronunciation")

        lbl_pos = tk.Label(self.frame_write, text="■ 品詞 (Part of Speech)", font=("Consolas", 10, "bold"), anchor="w")
        lbl_pos.pack(anchor="w")
        self.entry_labels.append(lbl_pos)
        
        self.pos_var = tk.StringVar(value=PART_OF_SPEECH_LIST[0])
        self.pos_menu = tk.OptionMenu(self.frame_write, self.pos_var, *PART_OF_SPEECH_LIST)
        self.pos_menu.config(relief="flat", highlightthickness=0, font=("Consolas", 11))
        self.pos_menu.pack(fill=tk.X, pady=(0, 10), ipady=3)
        self.widgets["pos_menu"] = self.pos_menu

        create_row("意味 (Meaning)", "meaning")
        create_row("使用例 (Example)", "example")

        btn_box = tk.Frame(self.frame_write, bg=self.colors["bg"], pady=15)
        btn_box.pack(fill=tk.X)
        self.widgets["btn_box"] = btn_box

        self.btn_save = tk.Button(btn_box, text="💾 SAVE", command=self.save_entry, relief="flat", padx=20, font=("Consolas", 10, "bold"))
        self.btn_save.pack(side=tk.LEFT, padx=5)
        self.widgets["btn_save"] = self.btn_save

        self.btn_clear = tk.Button(btn_box, text="CLEAR", command=self.clear_form, relief="flat", padx=10)
        self.btn_clear.pack(side=tk.LEFT, padx=5)
        self.widgets["btn_clear"] = self.btn_clear

        self.btn_delete = tk.Button(btn_box, text="🗑 DELETE", command=self.delete_entry, relief="flat", padx=10)
        self.btn_delete.pack(side=tk.RIGHT)
        self.widgets["btn_delete"] = self.btn_delete

    # ==========================================
    #  ★ 設定ダイアログ (NEW) ★
    # ==========================================
    def open_config_dialog(self):
        dlg = tk.Toplevel(self.root)
        dlg.title("Settings")
        dlg.geometry("400x300")
        c = self.colors
        dlg.configure(bg=c["bg"])
        
        # モーダルにする
        dlg.transient(self.root)
        dlg.grab_set()

        tk.Label(dlg, text="CONFIGURATION", font=("Consolas", 14, "bold"), 
                 bg=c["bg"], fg=c["fg"]).pack(pady=15)

        # --- テーマ設定 ---
        frame_theme = tk.LabelFrame(dlg, text="UI Theme", font=("Consolas", 10), 
                                    bg=c["bg"], fg=c["fg_dim"], relief="solid", bd=1)
        frame_theme.pack(fill=tk.X, padx=20, pady=5)

        self.var_theme = tk.StringVar(value=self.current_theme_name)
        
        def on_theme_change():
            # ラジオボタン切り替え時に即座にテーマを適用してプレビュー
            self.apply_temp_theme(self.var_theme.get(), dlg, [rb1, rb2, rb3, rb4])

        rb1 = tk.Radiobutton(frame_theme, text="Dark (Hacker)", variable=self.var_theme, value="Dark",
                       command=on_theme_change, bg=c["bg"], fg=c["fg"], selectcolor=c["bg"], font=("Consolas", 10))
        rb1.pack(side=tk.LEFT, padx=20, pady=10)
        
        rb2 = tk.Radiobutton(frame_theme, text="Light (Office)", variable=self.var_theme, value="Light",
                       command=on_theme_change, bg=c["bg"], fg=c["fg"], selectcolor=c["bg"], font=("Consolas", 10))
        rb2.pack(side=tk.LEFT, padx=20, pady=10)

        # --- スプラッシュ設定 ---
        frame_splash = tk.LabelFrame(dlg, text="Startup Splash Screen", font=("Consolas", 10),
                                     bg=c["bg"], fg=c["fg_dim"], relief="solid", bd=1)
        frame_splash.pack(fill=tk.X, padx=20, pady=5)

        self.var_splash = tk.StringVar(value=self.splash_style)

        rb3 = tk.Radiobutton(frame_splash, text="Classic (v1.0)", variable=self.var_splash, value="Classic",
                       bg=c["bg"], fg=c["fg"], selectcolor=c["bg"], font=("Consolas", 10))
        rb3.pack(side=tk.LEFT, padx=20, pady=10)
        
        rb4 = tk.Radiobutton(frame_splash, text="Modern (v2.0)", variable=self.var_splash, value="Modern",
                       bg=c["bg"], fg=c["fg"], selectcolor=c["bg"], font=("Consolas", 10))
        rb4.pack(side=tk.LEFT, padx=20, pady=10)

        # --- ボタン ---
        btn_frame = tk.Frame(dlg, bg=c["bg"], pady=20)
        btn_frame.pack()
        
        def save_config():
            # 保存
            new_theme = self.var_theme.get()
            new_splash = self.var_splash.get()
            
            self.db.set_setting("theme", new_theme)
            self.db.set_setting("splash_style", new_splash)
            
            self.current_theme_name = new_theme
            self.splash_style = new_splash
            self.colors = THEMES[new_theme]
            
            # メイン画面に適用
            self.apply_theme_to_root()
            self.apply_theme_to_widgets()
            
            self.log(f"Config Saved: {new_theme} / {new_splash}", "success")
            dlg.destroy()

        tk.Button(btn_frame, text="SAVE & CLOSE", command=save_config, 
                  bg=c["accent"], fg="white", font=("Consolas", 10, "bold"), relief="flat", padx=15).pack()

        # ダイアログ自体の色も初期設定
        self.apply_temp_theme(self.current_theme_name, dlg, [rb1, rb2, rb3, rb4])

    def apply_temp_theme(self, theme_name, dlg, rbs):
        """設定ダイアログでのプレビュー用"""
        c = THEMES[theme_name]
        dlg.configure(bg=c["bg"])
        for child in dlg.winfo_children():
            if isinstance(child, tk.LabelFrame):
                child.configure(bg=c["bg"], fg=c["fg_dim"])
            elif isinstance(child, tk.Label):
                child.configure(bg=c["bg"], fg=c["fg"])
            elif isinstance(child, tk.Frame):
                child.configure(bg=c["bg"])
        for rb in rbs:
            rb.configure(bg=c["bg"], fg=c["fg"], selectcolor=c["bg"], activebackground=c["bg"])


    # ==========================================
    #  テーマ適用処理 (メイン画面)
    # ==========================================
    def toggle_theme(self):
        # 簡易切替（ボタン用）
        new_theme = "Light" if self.current_theme_name == "Dark" else "Dark"
        self.current_theme_name = new_theme
        self.colors = THEMES[new_theme]
        self.db.set_setting("theme", new_theme)
        self.apply_theme_to_root()
        self.apply_theme_to_widgets()
        self.log(f"Theme switched to {new_theme}", "info")

    def apply_theme_to_widgets(self):
        c = self.colors
        frames = ["header_frame", "content_frame", "frame_read", "frame_write", "search_frame", 
                  "opt_frame", "left_group", "order_frame", "detail_frame", "btn_box", "log_frame"]
        for name in frames:
            if name in self.widgets: self.widgets[name].configure(bg=c["bg"])

        labels = ["lbl_search", "lbl_detail_term", "lbl_write_title", "lbl_log_title"]
        for name in labels:
            if name in self.widgets: self.widgets[name].configure(bg=c["bg"], fg=c["fg"])

        for lbl in self.entry_labels:
            lbl.configure(bg=c["bg"], fg=c["fg_dim"])

        # ボタン色
        btn_bg = c.get("btn_bg", "#333333")
        btn_fg = c.get("btn_fg", "#FFFFFF")
        
        self.btn_import.configure(bg=btn_bg, fg=btn_fg)
        self.btn_config.configure(bg=btn_bg, fg=btn_fg)
        
        self.btn_mode.configure(bg=c["accent"], fg="#FFFFFF")
        self.btn_up.configure(bg=btn_bg, fg=c["fg"])
        self.btn_down.configure(bg=btn_bg, fg=c["fg"])
        self.btn_save.configure(bg=c["accent"], fg="#FFFFFF")
        self.btn_clear.configure(bg="#444444" if self.current_theme_name=="Dark" else "#AAAAAA", fg="#FFFFFF")
        self.btn_delete.configure(bg="#CC0000", fg="#FFFFFF")

        entries = ["entry_search"] + [f"entry_{k}" for k in ["term", "pronunciation", "meaning", "example"]]
        for name in entries:
            if name in self.widgets:
                self.widgets[name].configure(bg=c["input_bg"], fg=c["input_fg"], insertbackground=c["fg"])

        self.listbox.configure(bg=c["list_bg"], fg=c["list_fg"], selectbackground=c["select_bg"], selectforeground=c["select_fg"])
        self.detail_text.configure(bg=c["bg"], fg=c["fg"])
        self.log_text.configure(bg="#050505" if self.current_theme_name=="Dark" else "#FFFFFF", fg=c["fg"])

        for rb in self.radios:
            rb.configure(bg=c["bg"], fg=c["fg"], selectcolor=c["bg"], activebackground=c["bg"], activeforeground=c["fg"])
        
        self.pos_menu.configure(bg=c["input_bg"], fg=c["fg"], activebackground=c["accent"], activeforeground="#FFFFFF")
        self.pos_menu["menu"].configure(bg=c["input_bg"], fg=c["fg"])

    # ==========================================
    #  その他ロジック
    # ==========================================
    def log(self, message, level="info"):
        self.log_text.config(state="normal")
        timestamp = time.strftime("[%H:%M:%S]")
        c = self.colors
        self.log_text.tag_config("info", foreground=c["log_fg_info"])
        self.log_text.tag_config("error", foreground=c["log_fg_err"])
        self.log_text.tag_config("success", foreground=c["accent"])
        self.log_text.tag_config("warn", foreground="#FFD700" if self.current_theme_name=="Dark" else "#FF8C00")
        self.log_text.insert(tk.END, f"{timestamp} ", "info")
        self.log_text.insert(tk.END, f"{message}\n", level)
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

    def import_json_dialog(self):
        filename = filedialog.askopenfilename(
            title="Import JSON to Database",
            filetypes=[("JSON", "*.json"), ("All", "*.*")],
            initialdir=os.getcwd()
        )
        if filename:
            self.import_json_logic(filename)

    def import_json_logic(self, filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = json.load(f)
            items_to_add = []
            if isinstance(content, list): items_to_add = content
            elif isinstance(content, dict):
                for k, v in content.items():
                    v['term'] = k
                    items_to_add.append(v)
            success_count = 0
            for item in items_to_add:
                term = item.get("term", item.get("word", ""))
                if term:
                    data = {
                        'term': term,
                        'pronunciation': item.get("pronunciation", ""),
                        'pos': item.get("part_of_speech", item.get("pos", "")),
                        'meaning': item.get("definition", item.get("meaning", "")),
                        'example': item.get("example", "")
                    }
                    self.db.upsert_word(data)
                    success_count += 1
            self.log(f"Imported/Updated {success_count} words from JSON.", "success")
            self.refresh_list()
        except Exception as e:
            self.log(f"Import Error: {e}", "error")

    def refresh_list(self, query=""):
        self.listbox.delete(0, tk.END)
        self.data_cache = self.db.get_all_words()
        query = query.lower()
        mode = self.search_mode.get()
        for item in self.data_cache:
            word = item['term']
            w_lower = word.lower()
            match = False
            if not query: match = True
            elif mode == "contains" and query in w_lower: match = True
            elif mode == "startswith" and w_lower.startswith(query): match = True
            elif mode == "endswith" and w_lower.endswith(query): match = True
            if match: self.listbox.insert(tk.END, word)

    def on_search(self, event=None):
        self.refresh_list(self.entry_search.get())

    def show_detail(self, event):
        sel = self.listbox.curselection()
        if not sel: return
        term = self.listbox.get(sel[0])
        item = next((x for x in self.data_cache if x['term'] == term), None)
        if not item: return
        self.lbl_detail_term.config(text=term)
        content = f"【発音】 {item['pronunciation']}\n【品詞】 {item['pos']}\n\n【意味】\n{item['meaning']}\n\n【例文】\n{item['example']}"
        self.detail_text.config(state="normal")
        self.detail_text.delete(1.0, tk.END)
        self.detail_text.insert(tk.END, content)
        self.detail_text.config(state="disabled")
        if self.current_mode == "write": self.fill_form(item)

    def save_entry(self):
        data = {
            'term': self.entries["term"].get().strip(),
            'pronunciation': self.entries["pronunciation"].get().strip(),
            'pos': self.pos_var.get(),
            'meaning': self.entries["meaning"].get().strip(),
            'example': self.entries["example"].get().strip()
        }
        if not data['term']:
            self.log("Term is required.", "warn")
            return
        result = self.db.upsert_word(data)
        self.refresh_list(self.entry_search.get())
        if result == "created": self.log(f"Registered: {data['term']}", "success")
        else: self.log(f"Updated: {data['term']}", "success")

    def delete_entry(self):
        term = self.entries["term"].get().strip()
        if not term: return
        if messagebox.askyesno("Delete", f"Really delete '{term}'?"):
            self.db.delete_word(term)
            self.clear_form()
            self.refresh_list(self.entry_search.get())
            self.log(f"Deleted: {term}", "warn")

    def fill_form(self, item):
        self.clear_form()
        self.entries["term"].insert(0, item['term'])
        self.entries["pronunciation"].insert(0, item['pronunciation'])
        self.entries["meaning"].insert(0, item['meaning'])
        self.entries["example"].insert(0, item['example'])
        self.pos_var.set(item['pos'])

    def clear_form(self):
        for k, ent in self.entries.items(): ent.delete(0, tk.END)
        self.pos_var.set(PART_OF_SPEECH_LIST[0])

    def toggle_mode(self):
        if self.current_mode == "read":
            self.frame_read.pack_forget()
            self.frame_write.pack(fill=tk.BOTH, expand=True)
            self.current_mode = "write"
            self.btn_mode.config(text="MODE: WRITE")
            try:
                sel = self.listbox.curselection()
                if sel:
                    term = self.listbox.get(sel[0])
                    item = next((x for x in self.data_cache if x['term'] == term), None)
                    if item: self.fill_form(item)
            except: pass
        else:
            self.frame_write.pack_forget()
            self.frame_read.pack(fill=tk.BOTH, expand=True)
            self.current_mode = "read"
            self.btn_mode.config(text="MODE: READ")

    def move_up(self): self._move_item(-1)
    def move_down(self): self._move_item(1)

    def _move_item(self, direction):
        if self.entry_search.get():
            self.log("Clear search before reordering.", "warn")
            return
        sel = self.listbox.curselection()
        if not sel: return
        idx = sel[0]
        target_idx = idx + direction
        if 0 <= target_idx < len(self.data_cache):
            item1 = self.data_cache[idx]
            item2 = self.data_cache[target_idx]
            self.db.update_order(item1['term'], item2['sort_order'], item2['term'], item1['sort_order'])
            self.refresh_list()
            self.listbox.selection_set(target_idx)
            self.listbox.see(target_idx)
            self.log(f"Moved '{item1['term']}'", "info")

if __name__ == "__main__":
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except: pass
    root = tk.Tk()
    app = ReDicSearcherApp(root)
    root.mainloop()