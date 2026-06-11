import os
import logging
from typing import TYPE_CHECKING
from PyQt5.QtWidgets import QSystemTrayIcon

from src.core.utils import get_lang_from_registry, load_locale, LOG_FILE
from src.core.app_launcher import AppLauncher
from src.ui.dialogs import GamingMessageBox, GamingLogViewerDialog

try:
    LANG = get_lang_from_registry()
    TEXTS = load_locale(LANG)
except Exception:
    LANG = os.getenv('GEFORCE_LANG', 'en')
    TEXTS = load_locale(LANG)

logger = logging.getLogger('geforce_presence')

if TYPE_CHECKING:
    from ..tray_icon import SystemTrayIcon
    Base = SystemTrayIcon
else:
    Base = object

class NavigationHandlerMixin(Base):
    def open_geforce(self):
        if not AppLauncher.launch_geforce_now():
            title = TEXTS.get("gfn_corrupted_title", "GeForce NOW Error")
            msg = TEXTS.get("gfn_install_question", "GeForce NOW is not installed or not found in the default path.\n\nDo you want to download and install GeForce NOW automatically now?")
            if GamingMessageBox.show_question(None, title, msg):
                self.on_gfn_error_detected()

    def open_discord(self):
        updater = AppLauncher.find_discord()
        if not updater:
            import psutil
            is_running = False
            for proc in psutil.process_iter(attrs=['name']):
                name = (proc.info.get('name') or "").lower()
                if "discord" in name and "update" not in name:
                    is_running = True
                    break
            if is_running:
                self.showMessage("Discord", TEXTS.get("already_running_discord", "💡 Discord ya se está ejecutando"), QSystemTrayIcon.Information, 3000)
            else:
                GamingMessageBox.show_warning(None, TEXTS.get("tray_open_discord", "Open Discord"), TEXTS.get("discord_not_found_msg", "Discord not found at the default location."))
        else:
            AppLauncher.launch_discord()

    def open_logs(self):
        try:
            dlg = GamingLogViewerDialog(texts=TEXTS, parent=None)
            dlg.exec_()
        except Exception as e:
            logger.error(f"Error opening custom log viewer: {e}")
            if LOG_FILE.exists():
                os.startfile(LOG_FILE)
            else:
                self.showMessage(TEXTS.get("logs_title", "Logs"), TEXTS.get("open_logs_error", "No log file found."), QSystemTrayIcon.Warning, 3000)
