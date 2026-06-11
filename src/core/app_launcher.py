import os
import psutil
import subprocess
import logging
import json
import time
import sys
from pathlib import Path
from typing import Optional
from src.core.utils import get_lang_from_registry, load_locale

try:
    LANG = get_lang_from_registry()
    TEXTS = load_locale(LANG)
except Exception:
    LANG = os.getenv('GEFORCE_LANG', 'en')
    TEXTS = load_locale(LANG)

logger = logging.getLogger('geforce_presence')

class AppLauncher:
    @staticmethod
    def find_geforce_now() -> Optional[str]:
        if sys.platform == "win32":
            possible = [
                Path(os.getenv("LOCALAPPDATA", "")) / "NVIDIA Corporation" / "GeForceNOW" / "CEF" / "GeForceNOW.exe"
            ]
            for p in possible:
                if p.exists():
                    return str(p)
        elif sys.platform == "darwin":
            p = Path("/Applications/GeForceNOW.app")
            if p.exists():
                return str(p)
        return None

    @staticmethod
    def _is_process_running_by_name(target_name: str) -> bool:
        try:
            for proc in psutil.process_iter(attrs=['name']):
                name = (proc.info.get('name') or "").lower()
                if name == target_name.lower() or target_name.lower() in name:
                    return True
        except Exception:
            pass
        return False

    @staticmethod
    def kill_process_by_name(target_name: str):
        try:
            for proc in psutil.process_iter(attrs=['name']):
                name = (proc.info.get('name') or "").lower()
                if name == target_name.lower() or target_name.lower() in name:
                    proc.kill()
        except Exception as e:
            logger.error(f"Error al cerrar {target_name}: {e}")

    @staticmethod
    def disable_native_rich_presence() -> tuple[bool, bool]:
        """
        Deshabilita el Rich Presence nativo de GeForce NOW:
        1. Modifica el archivo sharedstorage.json (discordRpEnabled = false).
        2. Renombra Discord.dll a Discord.dll.disabled.
        Retorna (success, modified)
        """
        if sys.platform != "win32":
            return False, False

        success = True
        modified = False

        # 1. Modificar sharedstorage.json
        config_path = Path(os.environ.get("LOCALAPPDATA", "")) / "NVIDIA Corporation" / "GeForceNOW" / "sharedstorage.json"
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"JSON corrupto o error de lectura: {e}")
                success = False
                data = None

            if data is not None:
                try:
                    if "appSettingsConfig" not in data:
                        data["appSettingsConfig"] = {}
                        
                    app_settings = data["appSettingsConfig"]
                    json_modified = False
                    
                    if "discordRpEnabled" not in app_settings or app_settings["discordRpEnabled"] is not False:
                        json_modified = True
                        
                    if json_modified:
                        new_app_settings = {}
                        for k, v in app_settings.items():
                            if k == "discordRpEnabled":
                                continue
                            new_app_settings[k] = v
                            if k == "clipboardPaste":
                                new_app_settings["discordRpEnabled"] = False
                                
                        if "discordRpEnabled" not in new_app_settings:
                            new_app_settings["discordRpEnabled"] = False
                            
                        data["appSettingsConfig"] = new_app_settings
                        
                        with open(config_path, "w", encoding="utf-8") as f:
                            json.dump(data, f, separators=(',', ':'))
                        logger.info("Flag discordRpEnabled deshabilitado en sharedstorage.json.")
                        modified = True
                except Exception as e:
                    logger.error(f"Error inesperado al procesar JSON: {e}")
                    success = False

        # 2. Renombrar Discord.dll
        dll_path = Path(os.environ.get("LOCALAPPDATA", "")) / "NVIDIA Corporation" / "GeForceNOW" / "CEF" / "cef" / "GeForceNOW" / "Discord.dll"
        if dll_path.exists():
            disabled_path = dll_path.with_name("Discord.dll.disabled")
            if disabled_path.exists():
                try:
                    disabled_path.unlink()
                except Exception:
                    pass
            try:
                dll_path.rename(disabled_path)
                modified = True
                logger.info("Plugin nativo Discord.dll renombrado a Discord.dll.disabled exitosamente.")
            except PermissionError:
                # El archivo está bloqueado por el proceso en ejecución
                logger.warning("Discord.dll está bloqueado (GeForce NOW en ejecución). Se reintentará tras detener el proceso.")
                modified = True
            except Exception as e:
                logger.error(f"Error renombrando Discord.dll: {e}")
                success = False

        return success, modified

    @staticmethod
    def launch_geforce_now() -> bool:
        success, modified = AppLauncher.disable_native_rich_presence()
        
        target_proc = "GeForceNOW.exe" if sys.platform == "win32" else "GeForceNOW"
        is_running = AppLauncher._is_process_running_by_name(target_proc)
        if sys.platform == "darwin" and not is_running:
            is_running = AppLauncher._is_process_running_by_name("GeForce NOW")
        
        if is_running:
            if modified and sys.platform == "win32":
                logger.info("Reiniciando GeForce NOW para aplicar la desactivación del Rich Presence nativo...")
                AppLauncher.kill_process_by_name("GeForceNOW.exe")
                time.sleep(1.5)  # Esperar a que se cierre completamente
                # Reintentar la desactivación ahora que el proceso está cerrado y el archivo no está bloqueado
                AppLauncher.disable_native_rich_presence()
            else:
                logger.info(TEXTS.get("already_running", "💡 GeForce NOW is already running"))
                return True

        path = AppLauncher.find_geforce_now()
        if path:
            logger.info(TEXTS.get("launching", "🚀 Launching GeForce NOW..."))
            if sys.platform == "darwin":
                subprocess.Popen(["open", "-a", path])
            else:
                subprocess.Popen([path])
            return True
        else:
            logger.error(TEXTS.get("geforce_not_found", "GeForce NOW not found in the default installation path."))
            return False

    @staticmethod
    def find_discord() -> Optional[str]:
        if sys.platform == "win32":
            p = Path(os.getenv("LOCALAPPDATA", "")) / "Discord" / "Update.exe"
            if p.exists():
                return str(p)
        elif sys.platform == "darwin":
            p = Path("/Applications/Discord.app")
            if p.exists():
                return str(p)
        return None

    @staticmethod
    def launch_discord():
        for proc in psutil.process_iter(attrs=['name']):
            name = (proc.info.get('name') or "").lower()
            if "discord" in name and "update" not in name:
                logger.info(TEXTS.get("already_running_discord", "💡 Discord ya está en ejecución"))
                return
        updater = AppLauncher.find_discord()
        if updater:
            logger.info(TEXTS.get("launching_discord", "🚀 Iniciando Discord..."))
            if sys.platform == "darwin":
                subprocess.Popen(["open", "-a", updater])
            else:
                subprocess.Popen([updater, "--processStart", "Discord.exe"])
        else:
            logger.warning("⚠️ No se encontró Discord instalado en la ruta por defecto.")
