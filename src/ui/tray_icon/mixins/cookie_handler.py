import os
import logging
from typing import TYPE_CHECKING
from PyQt5.QtWidgets import QSystemTrayIcon

from src.ui.dialogs import GamingMessageBox
from src.core.utils import get_lang_from_registry, load_locale

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

class CookieHandlerMixin(Base):
    def obtain_cookie(self):
        def confirm_callback(title, message):
            if title == "Cookie":
                choice = self.config_manager.get_setting("ask_cookie_choice")
                if choice == "yes":
                    return True
                elif choice == "no":
                    return False
                
                res, checked = GamingMessageBox.show_question(
                    None, 
                    title, 
                    message, 
                    checkbox_text=TEXTS.get("dont_show_again", "No mostrar de nuevo")
                )
                if checked:
                    self.config_manager.set_setting("ask_cookie_choice", "yes" if res else "no")
                return res

            elif "Edge" in message or "Chrome" in message or "open_confirm" in message or title == TEXTS.get("edge_open", "Microsoft Edge está abierto"):
                if self.config_manager.get_setting("always_close_browser", False):
                    return True
                
                res, checked = GamingMessageBox.show_question(
                    None, 
                    title, 
                    message, 
                    checkbox_text=TEXTS.get("always_close", "Cerrar siempre")
                )
                if checked and res:
                    self.config_manager.set_setting("always_close_browser", True)
                return res
            
            return GamingMessageBox.show_question(None, title, message)

        cookie, status_key = self.pm.cookie_manager.ask_and_obtain_cookie(confirm_callback)
        if cookie:
            self.pm.update_cookie(cookie)
            self.showMessage(TEXTS.get("cookie_title", "Cookie"), TEXTS.get("cookie_saved", "Cookie saved"), QSystemTrayIcon.Information, 3000)
            return

        if status_key == "cookie_err_cancelled":
            logger.info("El usuario canceló la obtención de cookie.")
            return

        err_msg = TEXTS.get(status_key, TEXTS.get("cookie_not_found", "Could not obtain cookie."))
        logger.warning(f"Error al obtener cookie de Steam automáticamente: {status_key} ({err_msg})")
        
        self.showMessage(TEXTS.get("cookie_title", "Cookie"), err_msg, QSystemTrayIcon.Warning, 4000)

        # Ask if they want to enter it manually
        ask_manual = GamingMessageBox.show_question(
            None,
            TEXTS.get("cookie_manual_title", "Manual Cookie Entry"),
            TEXTS.get("cookie_manual_prompt", "Automated cookie retrieval did not succeed. Do you want to enter the Steam cookie manually?")
        )

        if ask_manual:
            from src.ui.dialogs import GamingTextInputDialog
            cookie_val, ok = GamingTextInputDialog.get_text(
                None,
                TEXTS.get("cookie_manual_title", "Manual Cookie Entry"),
                TEXTS.get("cookie_manual_label", "Paste your 'steamLoginSecure' cookie value here:"),
                ""
            )
            if ok and cookie_val:
                if self.pm.cookie_manager.validar_cookie(cookie_val):
                    from src.core.utils import save_cookie_to_env, ENV_PATH
                    save_cookie_to_env(cookie_val, ENV_PATH)
                    self.pm.update_cookie(cookie_val)
                    logger.info("✅ Cookie obtenida mediante entrada manual (Origen: Manual Input).")
                    self.showMessage(TEXTS.get("cookie_title", "Cookie"), TEXTS.get("cookie_saved", "Cookie saved"), QSystemTrayIcon.Information, 3000)
                else:
                    GamingMessageBox.show_warning(
                        None,
                        TEXTS.get("cookie_title", "Cookie"),
                        TEXTS.get("cookie_invalid_msg", "The cookie entered is invalid or expired. Please check it and try again.")
                    )
