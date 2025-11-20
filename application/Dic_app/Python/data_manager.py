# data_manager.py
import json
import os
from tkinter import messagebox

from constants import DATA_FILE

# --- データ操作ロジック ---

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