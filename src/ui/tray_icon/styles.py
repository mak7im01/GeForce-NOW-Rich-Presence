TRAY_MENU_STYLESHEET = """
    QMenu {
        background-color: #1e1f22; /* Discord-like dark background */
        color: #dcddde;            /* Light gray text */
        border: 1px solid #111111;
        border-radius: 8px;
        padding: 5px;
    }
    QMenu::item {
        background-color: transparent;
        padding: 8px 24px 8px 9px;
        border-radius: 4px;
        margin: 2px 4px;
        font-family: 'TT Octosquares Trl Cnd';
        font-size: 13px;
        color: #dcddde;
    }
    QMenu::icon {
        left: 4px;
    }
    QMenu::item:selected {
        background-color: #045D0E;
        color: white;
        font-weight: bold;
    }
    QMenu::separator {
        height: 1px;
        background: #3f4145;
        margin: 6px 8px;
    }
"""


STATUS_FRAME_STYLESHEET = """
    QFrame#status_widget_frame {
        background-color: #111214;
        border-radius: 6px;
        margin: 4px 6px;
        padding: 4px;
    }
"""

STATUS_TITLE_STYLESHEET = """
    color: #ffffff;
    font-size: 16px;
    font-family: "TT Octosquares Trl Cnd";
    font-weight: bold;
    padding-bottom: 0px;
"""

STATUS_LABEL_STYLESHEET = """
    color: #dcddde;
    font-size: 13px;
    font-family: 'TT Octosquares Trl Cnd';
    font-weight: bold;
"""

MENU_ITEM_FRAME_STYLESHEET = """
    QFrame#menu_item_widget {
        background-color: transparent;
        border-radius: 4px;
    }
"""

MENU_ITEM_TEXT_DANGER = """
    color: #ff4d4d;
    font-size: 13px;
    font-family: 'TT Octosquares Trl Cnd';
    font-weight: bold;
"""

MENU_ITEM_TEXT_NORMAL = """
    color: #dcddde;
    font-size: 13px;
    font-family: 'TT Octosquares Trl Cnd';
    font-weight: normal;
"""
