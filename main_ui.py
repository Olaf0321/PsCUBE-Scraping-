# import sys
# import os
# import subprocess
# from PyQt5.QtWidgets import (
#     QApplication, QWidget, QPushButton, QTextEdit, QVBoxLayout, QHBoxLayout, QLabel
# )
# from PyQt5.QtCore import QThread, pyqtSignal, Qt
# from PyQt5.QtGui import QFont

# def set_playwright_browsers_path():
#     if getattr(sys, 'frozen', False):
#         exe_dir = os.path.dirname(sys.executable)
#     else:
#         exe_dir = os.path.dirname(os.path.abspath(__file__))
#     browsers_dir = os.path.join(exe_dir, "playwright-browsers")
#     os.environ["PLAYWRIGHT_BROWSERS_PATH"] = browsers_dir

# set_playwright_browsers_path()

# # --- サブプロセス実行用スレッド ---
# class ScriptRunner(QThread):
#     log_signal = pyqtSignal(str)
#     finished_signal = pyqtSignal()

#     def __init__(self, script_path):
#         super().__init__()
#         self.script_path = script_path
#         self.process = None
#         self._stop = False

#     def run(self):
#         try:
#             env = os.environ.copy()
#             env["PYTHONIOENCODING"] = "utf-8"
#             self.process = subprocess.Popen(
#                 [sys.executable, "-u", self.script_path],
#                 stdout=subprocess.PIPE,
#                 stderr=subprocess.STDOUT,
#                 bufsize=1,
#                 universal_newlines=True,
#                 encoding="utf-8",
#                 env=env
#             )
#             for line in self.process.stdout:
#                 if self._stop:
#                     break
#                 self.log_signal.emit(line)
#             self.process.stdout.close()
#             self.process.wait()
#         except Exception as e:
#             self.log_signal.emit(f"[ERROR] {e}\n")
#         self.finished_signal.emit()

#     def stop(self):
#         self._stop = True
#         if self.process and self.process.poll() is None:
#             self.process.terminate()
#             try:
#                 self.process.wait(timeout=2)
#             except subprocess.TimeoutExpired:
#                 self.process.kill()

# # --- メインUI ---
# class MainWindow(QWidget):
#     def __init__(self):
#         super().__init__()
#         self.setWindowTitle("PsCUBE Scraping Controller")
#         self.setGeometry(200, 200, 700, 500)
#         self.setStyleSheet(self.dark_stylesheet())
#         self.runner = None

#         # --- UIコンポーネント ---
#         self.log_area = QTextEdit()
#         self.log_area.setReadOnly(True)
#         self.log_area.setFont(QFont("Consolas", 10))
#         self.log_area.setStyleSheet("background-color: #232629; color: #e0e0e0;")

#         self.pachinko_btn = QPushButton("パチンコ取得")
#         self.slot_btn = QPushButton("スロット取得")
#         self.pachinko_send_btn = QPushButton("パチンコデータ送信")
#         self.slot_send_btn = QPushButton("スロットデータ送信")
#         self.stop_btn = QPushButton("停止")
#         self.stop_btn.setEnabled(False)

#         # --- レイアウト ---
#         btn_layout = QHBoxLayout()
#         btn_layout.addWidget(self.pachinko_btn)
#         btn_layout.addWidget(self.slot_btn)
#         btn_layout.addWidget(self.pachinko_send_btn)
#         btn_layout.addWidget(self.slot_send_btn)
#         btn_layout.addWidget(self.stop_btn)

#         main_layout = QVBoxLayout()
#         main_layout.addLayout(btn_layout)
#         main_layout.addWidget(QLabel("ログ:"))
#         main_layout.addWidget(self.log_area)
#         self.setLayout(main_layout)

#         # --- イベント ---
#         self.pachinko_btn.clicked.connect(lambda: self.run_script("pachinko_scrap.py"))
#         self.slot_btn.clicked.connect(lambda: self.run_script("slot_scrap.py"))
#         self.pachinko_send_btn.clicked.connect(lambda: self.run_script("pachinko_send_spreadsheet.py"))
#         self.slot_send_btn.clicked.connect(lambda: self.run_script("slot_send_spreadsheet.py"))
#         self.stop_btn.clicked.connect(self.stop_script)

#     def run_script(self, script):
#         if self.runner and self.runner.isRunning():
#             self.log_area.append("\n[INFO] 既にスクリプトが実行中です。停止してから再度実行してください。\n")
#             return
#         script_path = os.path.join(os.getcwd(), script)
#         if not os.path.exists(script_path):
#             self.log_area.append(f"[ERROR] スクリプトが見つかりません: {script}\n")
#             return
#         self.log_area.append(f"\n[INFO] スクリプト実行開始: {script}\n")
#         self.runner = ScriptRunner(script_path)
#         self.runner.log_signal.connect(self.append_log)
#         self.runner.finished_signal.connect(self.on_script_finished)
#         self.runner.start()
#         self.stop_btn.setEnabled(True)
#         self.set_buttons_enabled(False)

#     def stop_script(self):
#         if self.runner and self.runner.isRunning():
#             self.log_area.append("[INFO] スクリプト停止中...\n")
#             self.runner.stop()
#         else:
#             self.log_area.append("[INFO] 実行中のスクリプトはありません。\n")

#     def on_script_finished(self):
#         self.log_area.append("[INFO] スクリプトが終了しました。\n")
#         self.stop_btn.setEnabled(False)
#         self.set_buttons_enabled(True)

#     def append_log(self, text):
#         self.log_area.append(text.rstrip())
#         self.log_area.verticalScrollBar().setValue(self.log_area.verticalScrollBar().maximum())

#     def set_buttons_enabled(self, enabled):
#         self.pachinko_btn.setEnabled(enabled)
#         self.slot_btn.setEnabled(enabled)
#         self.pachinko_send_btn.setEnabled(enabled)
#         self.slot_send_btn.setEnabled(enabled)

#     def dark_stylesheet(self):
#         return """
#         QWidget {
#             background-color: #181a1b;
#             color: #e0e0e0;
#         }
#         QPushButton {
#             background-color: #232629;
#             color: #e0e0e0;
#             border: 1px solid #444;
#             border-radius: 6px;
#             padding: 8px 16px;
#             font-size: 15px;
#         }
#         QPushButton:hover {
#             background-color: #31363b;
#         }
#         QPushButton:pressed {
#             background-color: #1a1d1f;
#         }
#         QLabel {
#             color: #b0b0b0;
#             font-size: 13px;
#         }
#         QTextEdit {
#             background-color: #232629;
#             color: #e0e0e0;
#             border: 1px solid #444;
#             border-radius: 6px;
#         }
#         """

# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     window = MainWindow()
#     window.show()
#     sys.exit(app.exec_()) 
    
import tkinter as tk
from tkinter import scrolledtext
import threading
import subprocess
import os
import sys
import io

def set_playwright_browsers_path():
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
    else:
        exe_dir = os.path.dirname(os.path.abspath(__file__))
    browsers_dir = os.path.join(exe_dir, "playwright-browsers")
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = browsers_dir

set_playwright_browsers_path()


class ScriptRunner(threading.Thread):
    def __init__(self, script_path, on_finish, on_log):
        super().__init__(daemon=True)
        self.script_path = script_path
        self.on_finish = on_finish
        self.on_log = on_log
        self.process = None
        self._stop_event = threading.Event()

    def run(self):
        try:
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            self.process = subprocess.Popen(
                [sys.executable, "-u", self.script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
                universal_newlines=True,
                encoding="utf-8",
                env=env
            )
            for line in self.process.stdout:
                if self._stop_event.is_set():
                    break
                self.on_log(line)
            self.process.stdout.close()
            self.process.wait()
        except Exception as e:
            self.on_log(f"[ERROR] {e}\n")
        self.on_finish()

    def stop(self):
        self._stop_event.set()
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()


class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PsCUBE Scraping Controller")
        self.root.geometry("700x500")
        self.root.configure(bg="#181a1b")

        self.runner = None

        # --- Frame for Buttons ---
        btn_frame = tk.Frame(root, bg="#181a1b")
        btn_frame.pack(pady=10)

        self.pachinko_btn = self.create_button(btn_frame, "パチンコ取得", lambda: self.run_script("pachinko_scrap.py"))
        self.slot_btn = self.create_button(btn_frame, "スロット取得", lambda: self.run_script("slot_scrap.py"))
        self.pachinko_send_btn = self.create_button(btn_frame, "パチンコデータ送信", lambda: self.run_script("pachinko_send_spreadsheet.py"))
        self.slot_send_btn = self.create_button(btn_frame, "スロットデータ送信", lambda: self.run_script("slot_send_spreadsheet.py"))
        self.stop_btn = self.create_button(btn_frame, "停止", self.stop_script, state=tk.DISABLED)

        # Arrange buttons in a horizontal row
        self.pachinko_btn.grid(row=0, column=0, padx=5)
        self.slot_btn.grid(row=0, column=1, padx=5)
        self.pachinko_send_btn.grid(row=0, column=2, padx=5)
        self.slot_send_btn.grid(row=0, column=3, padx=5)
        self.stop_btn.grid(row=0, column=4, padx=5)

        # --- Log area ---
        tk.Label(root, text="ログ:", bg="#181a1b", fg="#b0b0b0", font=("Arial", 12)).pack(anchor='w', padx=10)
        self.log_area = scrolledtext.ScrolledText(root, height=20, font=("Consolas", 10), bg="#232629", fg="#e0e0e0",
                                                  insertbackground="white", state=tk.DISABLED, bd=0)
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def create_button(self, parent, text, command, state=tk.NORMAL):
        return tk.Button(parent, text=text, command=command, state=state,
                         bg="#232629", fg="#e0e0e0", activebackground="#31363b",
                         activeforeground="#ffffff", font=("Arial", 10),
                         relief=tk.FLAT, padx=10, pady=5)

    def run_script(self, script):
        if self.runner and self.runner.is_alive():
            self.append_log("[INFO] 既にスクリプトが実行中です。停止してから再度実行してください。\n")
            return
        script_path = os.path.join(os.getcwd(), script)
        if not os.path.exists(script_path):
            self.append_log(f"[ERROR] スクリプトが見つかりません: {script}\n")
            return
        self.append_log(f"\n[INFO] スクリプト実行開始: {script}\n")
        self.runner = ScriptRunner(script_path, self.on_script_finished, self.append_log)
        self.runner.start()
        self.stop_btn.config(state=tk.NORMAL)
        self.set_buttons_enabled(False)

    def stop_script(self):
        if self.runner and self.runner.is_alive():
            self.append_log("[INFO] スクリプト停止中...\n")
            self.runner.stop()
        else:
            self.append_log("[INFO] 実行中のスクリプトはありません。\n")

    def on_script_finished(self):
        self.append_log("[INFO] スクリプトが終了しました。\n")
        self.stop_btn.config(state=tk.DISABLED)
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

