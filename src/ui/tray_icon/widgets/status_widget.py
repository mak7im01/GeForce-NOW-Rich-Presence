from PyQt5.QtWidgets import QLabel, QWidgetAction, QFrame, QHBoxLayout, QVBoxLayout
from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtGui import QPixmap, QPainter, QColor, QBrush, QFont

from ..constants import ASSETS_DIR
from ..styles import STATUS_FRAME_STYLESHEET, STATUS_TITLE_STYLESHEET, STATUS_LABEL_STYLESHEET

class PulsingDotWidget(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(24, 24)
        self.setAlignment(Qt.AlignCenter)
        self.state = "disconnected"
        self.load_icon()
        
    def start_animation(self):
        pass
        
    def stop_animation(self):
        pass
        
    def set_state(self, state):
        if self.state != state:
            self.state = state
            self.update_icon()
            
    def load_icon(self):
        self.original_pixmap = None
        path = ASSETS_DIR / "iconos" / "gfn.svg"
        if not path.exists():
            path = ASSETS_DIR / "iconos" / "status.svg"
        if not path.exists():
            path = ASSETS_DIR / "geforce.ico"
            
        if path.exists():
            self.original_pixmap = QPixmap(str(path)).scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.update_icon()

    def tint_pixmap(self, pixmap, color):
        tinted = QPixmap(pixmap.size())
        tinted.fill(Qt.transparent)
        painter = QPainter(tinted)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.drawPixmap(0, 0, pixmap)
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter.fillRect(tinted.rect(), color)
        painter.end()
        return tinted

    def update_icon(self):
        if self.state == "active":
            color = QColor(0, 230, 118) # Green
        elif self.state == "forced":
            color = QColor(88, 101, 242) # Blue
        else:
            color = QColor(183, 28, 28) # Red

        if hasattr(self, "original_pixmap") and self.original_pixmap is not None:
            tinted = self.tint_pixmap(self.original_pixmap, color)
            self.setPixmap(tinted)
        else:
            # Draw a beautiful solid circle status dot directly
            pix = QPixmap(24, 24)
            pix.fill(Qt.transparent)
            painter = QPainter(pix)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.NoPen)
            # Center a 14x14 circle inside the 24x24 canvas
            painter.drawEllipse(5, 5, 14, 14)
            painter.end()
            self.setPixmap(pix)

class ElidedLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.full_text = text
        
    def setText(self, text):
        self.full_text = text
        self.update_elided_text()
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_elided_text()
        
    def update_elided_text(self):
        metrics = self.fontMetrics()
        w = max(100, self.width())
        elided = metrics.elidedText(self.full_text, Qt.ElideRight, w)
        super().setText(elided)

class StatusWidgetAction(QWidgetAction):
    def __init__(self, parent):
        super().__init__(parent)
        self.widget = QFrame()
        self.widget.setObjectName("status_widget_frame")
        self.widget.setStyleSheet(STATUS_FRAME_STYLESHEET)
        
        layout = QHBoxLayout(self.widget)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignVCenter)
        
        self.dot = PulsingDotWidget()
        
        text_vbox = QVBoxLayout()
        text_vbox.setContentsMargins(0, 0, 0, 0)
        text_vbox.setSpacing(2)
        
        self.label = ElidedLabel()
        self.label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        font = QFont("TT Octosquares Trl Cnd", 12, QFont.Bold)
        self.label.setFont(font)
        self.label.setStyleSheet(STATUS_TITLE_STYLESHEET)
        
        sub_layout = QHBoxLayout()
        sub_layout.setContentsMargins(0, 0, 0, 0)
        sub_layout.setSpacing(4)
        
        # Discord status elements
        self.discord_label = QLabel("DISCORD: ")
        self.discord_label.setStyleSheet(STATUS_LABEL_STYLESHEET)
        
        self.discord_icon_lbl = QLabel()
        self.discord_icon_lbl.setFixedSize(16, 16)
        self.discord_icon_lbl.setAlignment(Qt.AlignCenter)
        
        # GFN status elements
        self.gfn_label = QLabel("GFN: ")
        self.gfn_label.setStyleSheet(STATUS_LABEL_STYLESHEET)
        
        self.gfn_icon_lbl = QLabel()
        self.gfn_icon_lbl.setFixedSize(16, 16)
        self.gfn_icon_lbl.setAlignment(Qt.AlignCenter)
        
        sub_layout.addWidget(self.discord_label)
        sub_layout.addWidget(self.discord_icon_lbl)
        sub_layout.addSpacing(16)
        sub_layout.addWidget(self.gfn_label)
        sub_layout.addWidget(self.gfn_icon_lbl)
        sub_layout.addStretch()
        
        text_vbox.addWidget(self.label)
        text_vbox.addLayout(sub_layout)
        
        layout.addWidget(self.dot, alignment=Qt.AlignVCenter)
        layout.addLayout(text_vbox, 1)
        
        self.setDefaultWidget(self.widget)
        
    def start_animation(self):
        self.dot.start_animation()
        
    def stop_animation(self):
        self.dot.stop_animation()

    def tint_pixmap(self, pixmap, color):
        tinted = QPixmap(pixmap.size())
        tinted.fill(Qt.transparent)
        painter = QPainter(tinted)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.drawPixmap(0, 0, pixmap)
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter.fillRect(tinted.rect(), color)
        painter.end()
        return tinted
        
    def update_status(self, state, text, discord_connected=False, gfn_running=False):
        self.dot.set_state(state)
        self.label.setText(text)
        
        # Setup the dynamic SVGs for status indicators
        check_path = ASSETS_DIR / "iconos" / "status-check.svg"
        failed_path = ASSETS_DIR / "iconos" / "status-failed.svg"
        
        green_color = QColor(0, 230, 118)
        red_color = QColor(183, 28, 28)
        
        # 1. Update Discord status icon
        if discord_connected:
            if check_path.exists():
                pix = QPixmap(str(check_path)).scaled(16, 16, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.discord_icon_lbl.setPixmap(self.tint_pixmap(pix, green_color))
            else:
                self.discord_icon_lbl.setText("✔")
                self.discord_icon_lbl.setStyleSheet("color: #00e676; font-size: 14px; font-weight: bold;")
        else:
            if failed_path.exists():
                pix = QPixmap(str(failed_path)).scaled(16, 16, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.discord_icon_lbl.setPixmap(self.tint_pixmap(pix, red_color))
            else:
                self.discord_icon_lbl.setText("✘")
                self.discord_icon_lbl.setStyleSheet("color: #ff4d4d; font-size: 14px; font-weight: bold;")
                
        # 2. Update GFN status icon
        if gfn_running:
            if check_path.exists():
                pix = QPixmap(str(check_path)).scaled(16, 16, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.gfn_icon_lbl.setPixmap(self.tint_pixmap(pix, green_color))
            else:
                self.gfn_icon_lbl.setText("✔")
                self.gfn_icon_lbl.setStyleSheet("color: #00e676; font-size: 14px; font-weight: bold;")
        else:
            if failed_path.exists():
                pix = QPixmap(str(failed_path)).scaled(16, 16, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.gfn_icon_lbl.setPixmap(self.tint_pixmap(pix, red_color))
            else:
                self.gfn_icon_lbl.setText("✘")
                self.gfn_icon_lbl.setStyleSheet("color: #ff4d4d; font-size: 14px; font-weight: bold;")
