import threading
import tkinter as tk
from tkinter import scrolledtext
import os
import sys

# サブスクリプトをimport
import pachinko_scrap
import slot_scrap
import pachinko_send_spreadsheet
import slot_send_spreadsheet

def set_playwright_browsers_path():
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
    else:
        exe_dir = os.path.dirname(os.path.abspath(__file__))
    browsers_dir = os.path.join(exe_dir, "playwright-browsers")
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = browsers_dir

set_playwright_browsers_path()

class ScriptRunner(threading.Thread):
    def __init__(self, target_func, on_finish, on_log):
        super().__init__(daemon=True)
        self.target_func = target_func
        self.on_finish = on_finish
        self.on_log = on_log

    def run(self):
        try:
            self.target_func(self.on_log)
        except Exception as e:
            self.on_log(f"[ERROR] {e}\n")
        self.on_finish()

class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PsCUBE Scraping Controller")
        self.root.geometry("700x500")
        self.root.configure(bg="#181a1b")
        self.runner = None

        btn_frame = tk.Frame(root, bg="#181a1b")
        btn_frame.pack(pady=10)
        self.pachinko_btn = self.create_button(btn_frame, "パチンコ取得", self.run_pachinko)
        self.slot_btn = self.create_button(btn_frame, "スロット取得", self.run_slot)
        self.pachinko_send_btn = self.create_button(btn_frame, "パチンコデータ送信", self.run_pachinko_send)
        self.slot_send_btn = self.create_button(btn_frame, "スロットデータ送信", self.run_slot_send)
        self.pachinko_btn.grid(row=0, column=0, padx=5)
        self.slot_btn.grid(row=0, column=1, padx=5)
        self.pachinko_send_btn.grid(row=0, column=2, padx=5)
        self.slot_send_btn.grid(row=0, column=3, padx=5)

        tk.Label(root, text="ログ:", bg="#181a1b", fg="#b0b0b0", font=("Arial", 12)).pack(anchor='w', padx=10)
        self.log_area = scrolledtext.ScrolledText(root, height=20, font=("Consolas", 10), bg="#232629", fg="#e0e0e0",
                                                  insertbackground="white", state=tk.DISABLED, bd=0)
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def create_button(self, parent, text, command, state=tk.NORMAL):
        return tk.Button(parent, text=text, command=command, state=state,
                         bg="#232629", fg="#e0e0e0", activebackground="#31363b",
                         activeforeground="#ffffff", font=("Arial", 10),
                         relief=tk.FLAT, padx=10, pady=5)

    def run_script(self, func):
        if self.runner and self.runner.is_alive():
            self.append_log("[INFO] 既にスクリプトが実行中です。停止してから再度実行してください。\n")
            return
        self.append_log(f"\n[INFO] スクリプト実行開始: {func.__name__}\n")
        self.runner = ScriptRunner(func, self.on_script_finished, self.append_log)
        self.runner.start()
        self.set_buttons_enabled(False)

    def run_pachinko(self):
        self.run_script(pachinko_scrap.main)

    def run_slot(self):
        self.run_script(slot_scrap.main)

    def run_pachinko_send(self):
        self.run_script(pachinko_send_spreadsheet.main)

    def run_slot_send(self):
        self.run_script(slot_send_spreadsheet.main)

    def on_script_finished(self):
        self.append_log("[INFO] スクリプトが終了しました。\n")
        self.set_buttons_enabled(True)

    def append_log(self, text):
        def inner():
            self.log_area.config(state=tk.NORMAL)
            self.log_area.insert(tk.END, text)
            self.log_area.see(tk.END)
            self.log_area.config(state=tk.DISABLED)
        self.root.after(0, inner)

    def set_buttons_enabled(self, enabled):
        state = tk.NORMAL if enabled else tk.DISABLED
        self.pachinko_btn.config(state=state)
        self.slot_btn.config(state=state)
        self.pachinko_send_btn.config(state=state)
        self.slot_send_btn.config(state=state)

if __name__ == "__main__":
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()