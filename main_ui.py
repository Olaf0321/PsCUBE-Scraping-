import sys
import os
import subprocess
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QTextEdit, QVBoxLayout, QHBoxLayout, QLabel
)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QFont

# --- サブプロセス実行用スレッド ---
class ScriptRunner(QThread):
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, script_path):
        super().__init__()
        self.script_path = script_path
        self.process = None
        self._stop = False

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
                if self._stop:
                    break
                self.log_signal.emit(line)
            self.process.stdout.close()
            self.process.wait()
        except Exception as e:
            self.log_signal.emit(f"[ERROR] {e}\n")
        self.finished_signal.emit()

    def stop(self):
        self._stop = True
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()

# --- メインUI ---
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PsCUBE Scraping Controller")
        self.setGeometry(200, 200, 700, 500)
        self.setStyleSheet(self.dark_stylesheet())
        self.runner = None

        # --- UIコンポーネント ---
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setFont(QFont("Consolas", 10))
        self.log_area.setStyleSheet("background-color: #232629; color: #e0e0e0;")

        self.pachinko_btn = QPushButton("パチンコ取得")
        self.slot_btn = QPushButton("スロット取得")
        self.pachinko_send_btn = QPushButton("パチンコデータ送信")
        self.slot_send_btn = QPushButton("スロットデータ送信")
        self.stop_btn = QPushButton("停止")
        self.stop_btn.setEnabled(False)

        # --- レイアウト ---
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.pachinko_btn)
        btn_layout.addWidget(self.slot_btn)
        btn_layout.addWidget(self.pachinko_send_btn)
        btn_layout.addWidget(self.slot_send_btn)
        btn_layout.addWidget(self.stop_btn)

        main_layout = QVBoxLayout()
        main_layout.addLayout(btn_layout)
        main_layout.addWidget(QLabel("ログ:"))
        main_layout.addWidget(self.log_area)
        self.setLayout(main_layout)

        # --- イベント ---
        self.pachinko_btn.clicked.connect(lambda: self.run_script("pachinko_scrap.py"))
        self.slot_btn.clicked.connect(lambda: self.run_script("slot_scrap.py"))
        self.pachinko_send_btn.clicked.connect(lambda: self.run_script("pachinko_send_spreadsheet.py"))
        self.slot_send_btn.clicked.connect(lambda: self.run_script("slot_send_spreadsheet.py"))
        self.stop_btn.clicked.connect(self.stop_script)

    def run_script(self, script):
        if self.runner and self.runner.isRunning():
            self.log_area.append("\n[INFO] 既にスクリプトが実行中です。停止してから再度実行してください。\n")
            return
        script_path = os.path.join(os.getcwd(), script)
        if not os.path.exists(script_path):
            self.log_area.append(f"[ERROR] スクリプトが見つかりません: {script}\n")
            return
        self.log_area.append(f"\n[INFO] スクリプト実行開始: {script}\n")
        self.runner = ScriptRunner(script_path)
        self.runner.log_signal.connect(self.append_log)
        self.runner.finished_signal.connect(self.on_script_finished)
        self.runner.start()
        self.stop_btn.setEnabled(True)
        self.set_buttons_enabled(False)

    def stop_script(self):
        if self.runner and self.runner.isRunning():
            self.log_area.append("[INFO] スクリプト停止中...\n")
            self.runner.stop()
        else:
            self.log_area.append("[INFO] 実行中のスクリプトはありません。\n")

    def on_script_finished(self):
        self.log_area.append("[INFO] スクリプトが終了しました。\n")
        self.stop_btn.setEnabled(False)
        self.set_buttons_enabled(True)

    def append_log(self, text):
        self.log_area.append(text.rstrip())
        self.log_area.verticalScrollBar().setValue(self.log_area.verticalScrollBar().maximum())

    def set_buttons_enabled(self, enabled):
        self.pachinko_btn.setEnabled(enabled)
        self.slot_btn.setEnabled(enabled)
        self.pachinko_send_btn.setEnabled(enabled)
        self.slot_send_btn.setEnabled(enabled)

    def dark_stylesheet(self):
        return """
        QWidget {
            background-color: #181a1b;
            color: #e0e0e0;
        }
        QPushButton {
            background-color: #232629;
            color: #e0e0e0;
            border: 1px solid #444;
            border-radius: 6px;
            padding: 8px 16px;
            font-size: 15px;
        }
        QPushButton:hover {
            background-color: #31363b;
        }
        QPushButton:pressed {
            background-color: #1a1d1f;
        }
        QLabel {
            color: #b0b0b0;
            font-size: 13px;
        }
        QTextEdit {
            background-color: #232629;
            color: #e0e0e0;
            border: 1px solid #444;
            border-radius: 6px;
        }
        """

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_()) 