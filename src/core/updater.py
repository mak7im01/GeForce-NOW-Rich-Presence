import sys
import os
import logging
import requests
import subprocess
import tempfile
import time
from pathlib import Path
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QProgressBar, QMessageBox, QHBoxLayout,
    QScrollArea
)
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QObject

from src.version import VERSION
from src.utils.i18n import t
from src.core.utils import ASSETS_DIR
from PyQt5.QtGui import QIcon

# Common Stylesheet to match the rest of the app (Copied from dialogs.py to avoid circular imports)
GAMING_STYLESHEET = """
    QDialog {
        background-color: #0d0e10;
        border: 2px solid #1b1f23;
        border-radius: 14px;
    }

    QLabel {
        font-size: 14px;
        font-family: "Segoe UI";
        color: #e0e0e0;
        padding-bottom: 4px;
    }
    
    QLabel#title_label {
        font-size: 18px;
        font-weight: bold;
        color: #ffffff;
        padding-bottom: 8px;
    }

    QLineEdit, QSpinBox {
        padding: 8px;
        font-size: 14px;
        border: 1px solid #2c2f33;
        border-radius: 6px;
        background: #1a1b1d;
        color: #ffffff;
        font-family: "Segoe UI";
        font-weight: bold;
    }

    QLineEdit:focus, QSpinBox:focus {
        border: 2px solid #454C55;
    }

    QPushButton {
        background-color: #045D0E;
        color: #FFFFFF;
        padding: 8px 16px;
        border-radius: 6px;
        font-size: 14px;
        font-family: "Segoe UI";
        font-weight: bold;
    }

    QPushButton:hover {
        background-color: #12881F;
    }
    
    QPushButton:pressed {
        background-color: #03420a;
    }

    QPushButton#secondary {
        background-color: #2c2f33;
        color: #e6e6e6;
    }

    QPushButton#secondary:hover {
        background-color: #3c3f43;
    }

    /* LIST WIDGET & SCROLLBARS */
    QListWidget {
        background: #131416;
        border: 1px solid #1f2428;
        border-radius: 8px;
        padding: 6px;
        font-size: 13px;
        font-family: Consolas, monospace;
        color: #cfcfcf;
    }

    QListWidget::item {
        padding: 8px;
        border-radius: 4px;
        color: #dfdfdf;
    }

    QListWidget::item:selected {
        background-color: #00e676;
        color: #0e0f11;
        font-weight: bold;
    }

    QScrollBar:vertical {
        background: transparent;
        width: 8px;
        margin: 4px 0;
    }
    QScrollBar::handle:vertical {
        background: #383a3d;
        border-radius: 4px;
        min-height: 30px;
    }
    QScrollBar::handle:vertical:hover {
        background: #4a4d50;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0; 
        background: none; 
    }
"""

logger = logging.getLogger('geforce_presence')

def get_current_lang():
    try:
        from src.core.utils import get_lang_from_registry
        return get_lang_from_registry()
    except Exception:
        return os.getenv('GEFORCE_LANG', 'en')

def filter_release_notes(body: str, lang: str) -> str:
    if not body:
        return ""
    
    import re
    tags = re.findall(r'\[([a-zA-Z]{2})\]', body)
    if not tags:
        return body
        
    lang_upper = lang.upper()
    tags_upper = [t.upper() for t in tags]
    
    if lang_upper in tags_upper:
        target_tag = lang_upper
    elif 'EN' in tags_upper:
        target_tag = 'EN'
    else:
        target_tag = tags[0].upper()
        
    pattern = r'\[[a-zA-Z]{2}\]'
    parts = re.split(pattern, body)
    
    for i, tag in enumerate(tags):
        if tag.upper() == target_tag:
            return parts[i+1].strip()
            
    return body

GITHUB_RELEASES_URL = "https://api.github.com/repos/KarmaDevz/GeForce-NOW-Rich-Presence/releases/latest"

def parse_version(v_str):
    #"Simple semantic version parser ('1.0.0' -> (1, 0, 0))"
    try:
        return tuple(map(int, v_str.lstrip('v').split('.')))
    except Exception:
        return (0, 0, 0)

class UpdateWorker(QThread):
    check_finished = pyqtSignal(bool, str, str, str) # has_update, version, url, release_notes
    download_progress = pyqtSignal(int)
    download_finished = pyqtSignal(str) # path to installer
    error_occurred = pyqtSignal(str)

    def __init__(self, mode="check", download_url=None):
        super().__init__()
        self.mode = mode
        self.download_url = download_url

    def run(self):
        if self.mode == "check":
            self.check_updates()
        elif self.mode == "download":
            self.download_update()

    def check_updates(self):
        try:
            logger.info("📦 Buscando actualizaciones...")
            response = requests.get(GITHUB_RELEASES_URL, timeout=10)
            response.raise_for_status()
            data = response.json()

            latest_version_str = data.get("tag_name", "v0.0.0")
            latest_version = parse_version(latest_version_str)
            current_version = parse_version(VERSION)
            
            logger.info(f"📦 Version actual: {VERSION}, Última versión GitHub: {latest_version_str}")

            if latest_version > current_version:
                from src.core.utils import IS_WINDOWS, IS_MACOS, IS_LINUX
                update_url = None
                
                # Buscar asset de actualización silenciosa específico para la plataforma
                for asset in data.get("assets", []):
                    name_lower = asset["name"].lower()
                    if IS_WINDOWS and name_lower.endswith(".zip") and "windows" in name_lower:
                        update_url = asset["browser_download_url"]
                        logger.info("Encontrado asset de actualización silenciosa de Windows (.zip).")
                        break
                    elif IS_MACOS and name_lower.endswith(".zip") and "macos" in name_lower:
                        update_url = asset["browser_download_url"]
                        logger.info("Encontrado asset de actualización silenciosa de macOS (.zip).")
                        break
                    elif IS_LINUX and name_lower.endswith(".tar.gz") and "linux" in name_lower:
                        update_url = asset["browser_download_url"]
                        logger.info("Encontrado asset de actualización silenciosa de Linux (.tar.gz).")
                        break
                
                if not update_url and IS_WINDOWS:
                    for asset in data.get("assets", []):
                        if asset["name"].lower().endswith(".exe"):
                            update_url = asset["browser_download_url"]
                            logger.info("Encontrado instalador de actualización de Windows (.exe).")
                            break
                
                if update_url:
                    self.check_finished.emit(True, latest_version_str, update_url, data.get("body", ""))
                else:
                    logger.warning("Nueva versión encontrada pero no se encontró un archivo de actualización compatible para la plataforma.")
                    self.check_finished.emit(False, "", "", "")
            else:
                self.check_finished.emit(False, "", "", "")

        except Exception as e:
            logger.error(f"Error al buscar actualizaciones: {e}")
            self.error_occurred.emit(str(e))

    def download_update(self):
        try:
            logger.info(f"Descargando actualización desde {self.download_url}")
            response = requests.get(self.download_url, stream=True, timeout=30)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            
            tmp_dir = Path(tempfile.gettempdir()) / "geforce_update"
            tmp_dir.mkdir(parents=True, exist_ok=True)
            
            ext = ".zip" if self.download_url.lower().endswith(".zip") else ".exe"
            installer_path = tmp_dir / f"update{ext}"

            with open(installer_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        if total_size > 0:
                            progress = int((downloaded_size / total_size) * 100)
                            self.download_progress.emit(progress)

            self.download_finished.emit(str(installer_path))

        except Exception as e:
            logger.error(f"Error al descargar actualización: {e}")
            self.error_occurred.emit(str(e))

class UpdateDialog(QDialog):
    def __init__(self, version, url, release_notes, parent=None):
        super().__init__(parent)
        self.version = version
        self.url = url
        self.ignore_clicked = False
        self.setWindowTitle(t.get("update_available_title", "Update Available"))
        self.setWindowIcon(QIcon(str(ASSETS_DIR / "geforce.ico")))
        self.setFixedSize(400, 300)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setStyleSheet(GAMING_STYLESHEET)

        layout = QVBoxLayout()

        lbl_title = QLabel(f"<b>{t.get('new_version_found', 'New version found:')} {version}</b>")
        lbl_title.setObjectName("title_label")
        lbl_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_title)

        lbl_notes = QLabel(t.get("release_notes", "Release Notes:"))
        layout.addWidget(lbl_notes)

        self.notes_area = QScrollArea()
        self.notes_area.setWidgetResizable(True)
        self.notes_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        lang = get_current_lang()
        filtered_notes = filter_release_notes(release_notes, lang)

        self.notes_box = QLabel(filtered_notes)
        self.notes_box.setWordWrap(True)
        self.notes_box.setStyleSheet("background-color: #1a1b1d; padding: 10px; border-radius: 5px; color: #cfcfcf; border: 1px solid #2c2f33;")
        self.notes_box.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        self.notes_area.setWidget(self.notes_box)
        layout.addWidget(self.notes_area)
        
        layout.addStretch()

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        btn_layout = QHBoxLayout()
        self.btn_update = QPushButton(t.get("update_now", "Update Now"))
        self.btn_update.clicked.connect(self.start_download)
        self.btn_cancel = QPushButton(t.get("ignore_for_now", "Ignore for now"))
        self.btn_cancel.setObjectName("secondary")
        self.btn_cancel.clicked.connect(self.on_ignore_clicked)

        btn_layout.addWidget(self.btn_update)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

        self.worker = None

    def on_ignore_clicked(self):
        self.ignore_clicked = True
        self.reject()

    def start_download(self):
        self.btn_update.setEnabled(False)
        self.btn_cancel.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        self.worker = UpdateWorker(mode="download", download_url=self.url)
        self.worker.download_progress.connect(self.progress_bar.setValue)
        self.worker.download_finished.connect(self.install_update)
        self.worker.error_occurred.connect(self.on_error)
        self.worker.start()

    def install_update(self, installer_path):
        try:
            logger.info(f"Launching installer: {installer_path}")
            
            if installer_path.lower().endswith(".zip") or installer_path.lower().endswith(".tar.gz"):
                if getattr(sys, "frozen", False):
                    from src.core.utils import IS_WINDOWS, IS_MACOS, IS_LINUX
                    pid = os.getpid()
                    archive_path = str(installer_path)
                    install_dir = str(Path(sys.executable).parent)
                    exe_path = str(sys.executable)
                    
                    if IS_WINDOWS:
                        # PowerShell auto-update for Windows
                        powershell_cmd = (
                            f"Start-Sleep -Seconds 1; "
                            f"while (Get-Process -Id {pid} -ErrorAction SilentlyContinue) {{ Start-Sleep -Milliseconds 100 }}; "
                            f"Expand-Archive -Path '{archive_path}' -DestinationPath '{install_dir}' -Force; "
                            f"Remove-Item -Path '{archive_path}' -Force; "
                            f"Start-Process -FilePath '{exe_path}'"
                        )
                        logger.info(f"Ejecutando auto-actualizador silencioso en segundo plano (Windows): {powershell_cmd}")
                        subprocess.Popen(
                            ["powershell", "-Command", powershell_cmd],
                            creationflags=subprocess.CREATE_NO_WINDOW
                        )
                        sys.exit(0)
                        
                    elif IS_MACOS:
                        # Bash auto-update for macOS (using unzip)
                        bash_cmd = (
                            f"sleep 1; "
                            f"while kill -0 {pid} 2>/dev/null; do sleep 0.1; done; "
                            f"unzip -o '{archive_path}' -d '{install_dir}'; "
                            f"rm '{archive_path}'; "
                            f"open '{exe_path}'"
                        )
                        logger.info(f"Ejecutando auto-actualizador silencioso en segundo plano (macOS): {bash_cmd}")
                        subprocess.Popen(["bash", "-c", bash_cmd])
                        sys.exit(0)
                        
                    elif IS_LINUX:
                        # Bash auto-update for Linux (using tar)
                        bash_cmd = (
                            f"sleep 1; "
                            f"while kill -0 {pid} 2>/dev/null; do sleep 0.1; done; "
                            f"tar -xzf '{archive_path}' -C '{install_dir}'; "
                            f"rm '{archive_path}'; "
                            f"chmod +x '{exe_path}'; "
                            f"'{exe_path}' &"
                        )
                        logger.info(f"Ejecutando auto-actualizador silencioso en segundo plano (Linux): {bash_cmd}")
                        subprocess.Popen(["bash", "-c", bash_cmd])
                        sys.exit(0)
                else:
                    msg = f"Modo de desarrollo: Actualización descargada en {installer_path}.\nLa auto-actualización silenciosa solo funciona en la versión compilada."
                    logger.info(msg)
                    QMessageBox.information(self, "Desarrollo", msg)
                    self.accept()
            else:
                # Launch installer wizard (.exe) on Windows if not a zip and exit
                subprocess.Popen([installer_path], shell=True)
                sys.exit(0)
        except Exception as e:
            self.on_error(f"Failed to launch installer: {e}")

    def on_error(self, msg):
        QMessageBox.critical(self, "Error", msg)
        self.btn_update.setEnabled(True)
        self.btn_cancel.setEnabled(True)
        self.progress_bar.setVisible(False)

class Updater(QObject):
    update_status_changed = pyqtSignal()

    def __init__(self, config_manager=None, parent_widget=None):
        super().__init__()
        self.config_manager = config_manager
        self.parent_widget = parent_widget
        self.worker = None
        self.checking_updates = False
        self.update_available = False
        self.update_version = ""
        self.update_url = ""
        self.update_notes = ""
        self.active_dialog = None

    def check_for_updates(self, silent=True):
        if self.checking_updates:
            logger.info("Comprobación de actualizaciones ya en curso. Ignorando nueva solicitud.")
            return
        self.checking_updates = True
        self.worker = UpdateWorker(mode="check")
        self.worker.check_finished.connect(lambda has_update, ver, url, notes: self.on_check_finished(has_update, ver, url, notes, silent))
        self.worker.error_occurred.connect(lambda msg: self.on_check_error(msg, silent))
        self.worker.start()

    def on_check_finished(self, has_update, version, url, notes, silent):
        try:
            if has_update:
                self.update_available = True
                self.update_version = version
                self.update_url = url
                self.update_notes = notes
                self.update_status_changed.emit()

                # If silent, check if this version was already ignored and the time hasn't expired yet
                if silent and self.config_manager:
                    current_time = time.time()
                    last_ignored = self.config_manager.get_setting("updater_last_ignored_version", "")
                    ignore_until = self.config_manager.get_setting("updater_ignore_until", 0.0)
                    
                    if last_ignored == version and current_time < ignore_until:
                        logger.info(f"Actualización automática a {version} pospuesta hasta {time.ctime(ignore_until)} (ignorado).")
                        return

                self.show_update_dialog()
            else:
                self.update_available = False
                self.update_version = ""
                self.update_url = ""
                self.update_notes = ""
                self.update_status_changed.emit()
                if not silent:
                    QMessageBox.information(self.parent_widget, t.get("no_updates", "No Updates"), t.get("latest_version_msg", "You are using the latest version."))
        finally:
            self.checking_updates = False

    def on_check_error(self, msg, silent):
        try:
            if not silent:
                QMessageBox.critical(self.parent_widget, "Error", f"Error al comprobar actualizaciones: {msg}")
        finally:
            self.checking_updates = False

    def show_update_dialog(self):
        if not self.update_available:
            return

        if self.active_dialog is not None:
            try:
                self.active_dialog.raise_()
                self.active_dialog.activateWindow()
                return
            except RuntimeError:
                self.active_dialog = None

        self.active_dialog = UpdateDialog(self.update_version, self.update_url, self.update_notes, self.parent_widget)
        self.active_dialog.exec_()
        
        ignore_clicked = self.active_dialog.ignore_clicked
        self.active_dialog = None
        
        if ignore_clicked:
            self.save_ignore_settings(self.update_version)
            self.update_status_changed.emit()

    def save_ignore_settings(self, version):
        if not self.config_manager:
            return
        
        current_time = time.time()
        last_ignored = self.config_manager.get_setting("updater_last_ignored_version", "")
        next_ignore_days = self.config_manager.get_setting("updater_next_ignore_days", 7)
        
        # Reset count if it's a new version
        if last_ignored != version:
            next_ignore_days = 7
        
        # postpone duration
        ignore_until = current_time + (next_ignore_days * 24 * 60 * 60)
        
        # next ignore duration
        escalated_next_days = min(next_ignore_days + 7, 21)
        
        self.config_manager.set_setting("updater_last_ignored_version", version)
        self.config_manager.set_setting("updater_next_ignore_days", escalated_next_days)
        self.config_manager.set_setting("updater_ignore_until", ignore_until)
        
        logger.info(f"Actualización a {version} ignorada por {next_ignore_days} días (hasta {time.ctime(ignore_until)}). Próximo aplazamiento será de {escalated_next_days} días.")
    