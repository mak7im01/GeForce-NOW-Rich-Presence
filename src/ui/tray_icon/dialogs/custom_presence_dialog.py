from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QSpinBox
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from src.core.utils import ASSETS_DIR
from src.ui.dialogs import GAMING_STYLESHEET

class CustomPresenceDialog(QDialog):
    def __init__(self, game_name, current_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Custom Presence: {game_name}")
        self.setWindowIcon(QIcon(str(ASSETS_DIR / "geforce.ico")))
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.setStyleSheet(GAMING_STYLESHEET)
        
        self.game_name = game_name
        self.result_data = None
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Helper to create rows
        def add_row(label_txt, widget):
            r = QVBoxLayout()
            r.setSpacing(5)
            l = QLabel(label_txt)
            r.addWidget(l)
            r.addWidget(widget)
            layout.addLayout(r)
            return widget

        self.details_edit = add_row("Detalles (Línea 1):", QLineEdit())
        self.details_edit.setPlaceholderText("Ej: Jugando Competitivo")
        self.details_edit.setText(current_data.get("custom_details", ""))

        self.state_edit = add_row("Estado (Línea 2):", QLineEdit())
        self.state_edit.setPlaceholderText("Ej: En grupo de 5")
        self.state_edit.setText(current_data.get("custom_state", ""))

        # Party Size Row
        party_layout = QHBoxLayout()
        
        self.party_current = QSpinBox()
        self.party_current.setRange(0, 100)
        self.party_current.setValue(current_data.get("custom_party_size_current", 0))
        
        self.party_max = QSpinBox()
        self.party_max.setRange(0, 100)
        self.party_max.setValue(current_data.get("custom_party_size_max", 0))
        
        p_sub = QVBoxLayout()
        p_sub.addWidget(QLabel("Personas (Actual):"))
        p_sub.addWidget(self.party_current)
        party_layout.addLayout(p_sub)
        
        p_sub2 = QVBoxLayout()
        p_sub2.addWidget(QLabel("Personas (Max):"))
        p_sub2.addWidget(self.party_max)
        party_layout.addLayout(p_sub2)
        
        layout.addLayout(party_layout)
        
        layout.addWidget(QLabel("Nota: Si 'Max' es 0, no se mostrará información de grupo."))

        # Buttons
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Guardar")
        self.save_btn.clicked.connect(self.on_save)
        
        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.setObjectName("secondary")
        self.cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        self.adjustSize()

    def on_save(self):
        self.result_data = {
            "custom_details": self.details_edit.text(),
            "custom_state": self.state_edit.text(),
            "custom_party_size_current": self.party_current.value(),
            "custom_party_size_max": self.party_max.value()
        }
        self.accept()
