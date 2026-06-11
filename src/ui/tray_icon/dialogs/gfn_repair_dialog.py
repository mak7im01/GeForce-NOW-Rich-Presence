import os
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QHBoxLayout, QPushButton
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

from ..constants import ASSETS_DIR
from src.ui.dialogs import GAMING_STYLESHEET
from src.core.utils import get_lang_from_registry, load_locale

try:
    LANG = get_lang_from_registry()
    TEXTS = load_locale(LANG)
except Exception:
    LANG = os.getenv('GEFORCE_LANG', 'en')
    TEXTS = load_locale(LANG)

class GFNRepairDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(TEXTS.get("repair_title", "Repairing GeForce NOW"))
        self.setWindowIcon(QIcon(str(ASSETS_DIR / "geforce.ico")))
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.setFixedSize(450, 180)
        self.setStyleSheet(GAMING_STYLESHEET)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)
        
        # Title
        title_lbl = QLabel(TEXTS.get("repair_title", "Repairing GeForce NOW"))
        title_lbl.setObjectName("title_label")
        title_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_lbl)
        
        # Status text
        self.status_lbl = QLabel(TEXTS.get("repair_status_init", "Starting repair..."))
        self.status_lbl.setAlignment(Qt.AlignCenter)
        self.status_lbl.setStyleSheet("color: #cfcfcf;")
        layout.addWidget(self.status_lbl)
        
        # Progress Bar
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        self.progress.setAlignment(Qt.AlignCenter)
        self.progress.setStyleSheet("""
            QProgressBar {
                background-color: #1a1b1d;
                border: 1px solid #2c2f33;
                border-radius: 6px;
                color: #ffffff;
                font-weight: bold;
                text-align: center;
                height: 22px;
            }
            QProgressBar::chunk {
                background-color: #045D0E;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.progress)
        
        # Button layout (Hidden until error or done)
        self.btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton(TEXTS.get("close", "Close"))
        self.ok_btn.clicked.connect(self.accept)
        self.ok_btn.setVisible(False)
        self.btn_layout.addStretch()
        self.btn_layout.addWidget(self.ok_btn)
        self.btn_layout.addStretch()
        
        layout.addLayout(self.btn_layout)
        self.setLayout(layout)

    def on_progress(self, percent):
        self.progress.setValue(percent)

    def on_status(self, lang_key):
        self.status_lbl.setText(TEXTS.get(lang_key, lang_key))

    def on_error(self, err_msg):
        self.progress.setStyleSheet("""
            QProgressBar { background-color: #1a1b1d; border: 1px solid #d32f2f; border-radius: 6px; color: #ffffff; text-align: center; height: 22px; }
            QProgressBar::chunk { background-color: #d32f2f; border-radius: 4px; }
        """)
        msg = TEXTS.get("repair_status_error", "Error: {error}").replace("{error}", err_msg)
        self.status_lbl.setText(msg)
        self.status_lbl.setStyleSheet("color: #ff5252; font-weight: bold;")
        self.ok_btn.setVisible(True)

    def on_finished(self):
        self.status_lbl.setText(TEXTS.get("repair_status_done", "Repair completed."))
        self.status_lbl.setStyleSheet("color: #00e676; font-weight: bold;")
        self.progress.setValue(100)
        self.ok_btn.setVisible(True)
