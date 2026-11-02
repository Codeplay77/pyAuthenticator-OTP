"""
Theme Module for Python Authenticator

Provides the light and dark color palettes shared by every window and
matches the Windows title bar to the active theme.

Author: Codeplay
Date: November 2026
"""

import sys
from typing import Dict

if sys.platform == 'win32':
    import ctypes
    import winreg
    from ctypes import wintypes

    _user32 = ctypes.WinDLL('user32')
    _user32.GetParent.argtypes = [wintypes.HWND]
    _user32.GetParent.restype = wintypes.HWND

    _dwmapi = ctypes.WinDLL('dwmapi')
    _dwmapi.DwmSetWindowAttribute.argtypes = [
        wintypes.HWND, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD
    ]
    _dwmapi.DwmSetWindowAttribute.restype = ctypes.HRESULT


DWMWA_USE_IMMERSIVE_DARK_MODE = 20
DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1 = 19

PALETTES: Dict[str, Dict[str, str]] = {
    'light': {
        'bg': '#f3f5fa',
        'surface': '#ffffff',
        'surface_alt': '#f6f8fc',
        'shadow': '#e0e0e0',
        'border': '#dce2ee',
        'text': '#18243b',
        'text_secondary': '#53627b',
        'text_muted': '#62718a',
        'placeholder': '#dadce0',
        'accent': '#3659cf',
        'accent_soft': '#eaf0ff',
        'primary': '#3659cf',
        'primary_active': '#2947b1',
        'on_primary': '#ffffff',
        'header_subtitle': '#e3f2fd',
        'error': '#d93025',
        'error_soft': '#fce8e6',
        'danger': '#d93025',
        'danger_active': '#b52d20',
        'on_danger': '#ffffff',
        'warning': '#a85608',
        'success_soft': '#e7f4ec',
        'success': '#137333',
        'track': '#e8eaed',
        'scrollbar': '#dadce0',
        'scrollbar_active': '#bdc1c6',
    },
    'dark': {
        'bg': '#111722',
        'surface': '#1b2433',
        'surface_alt': '#222e40',
        'shadow': '#17181a',
        'border': '#344259',
        'text': '#edf2fc',
        'text_secondary': '#b1bed3',
        'text_muted': '#96a6bf',
        'placeholder': '#5f6368',
        'accent': '#a6bcff',
        'accent_soft': '#293c62',
        'primary': '#a6bcff',
        'primary_active': '#c0cfff',
        'on_primary': '#142044',
        'header_subtitle': '#3c4043',
        'error': '#f28b82',
        'error_soft': '#4a2f2d',
        'danger': '#f28b82',
        'danger_active': '#f6aea9',
        'on_danger': '#202124',
        'warning': '#f6be72',
        'success_soft': '#203d36',
        'success': '#81c995',
        'track': '#344259',
        'scrollbar': '#42536e',
        'scrollbar_active': '#627796',
    },
}


def system_prefers_dark() -> bool:
    """Return True when Windows is set to use dark mode for apps."""
    if sys.platform != 'win32':
        return False
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r'Software\Microsoft\Windows\CurrentVersion\Themes\Personalize'
        ) as key:
            value, _ = winreg.QueryValueEx(key, 'AppsUseLightTheme')
    except OSError:
        return False
    return value == 0


def resolve_theme(name: str) -> str:
    """Return the palette name for a ui.theme value.

    "light" and "dark" are used as is. Any other value, such as
    "system", follows the Windows app mode.
    """
    if name in PALETTES:
        return name
    return 'dark' if system_prefers_dark() else 'light'


def apply_title_bar(window, theme_name: str) -> None:
    """Use a dark Windows title bar for the dark theme (Windows 10 1809+)."""
    if sys.platform != 'win32':
        return
    window.update_idletasks()
    hwnd = _user32.GetParent(window.winfo_id())
    value = wintypes.BOOL(theme_name == 'dark')
    for attribute in (DWMWA_USE_IMMERSIVE_DARK_MODE,
                      DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1):
        try:
            result = _dwmapi.DwmSetWindowAttribute(
                hwnd, attribute, ctypes.byref(value), ctypes.sizeof(value)
            )
        except OSError:
            continue
        if result != 0:
            continue
        alpha = window.attributes('-alpha')
        window.attributes('-alpha', 0.99)
        window.attributes('-alpha', alpha)
        return
