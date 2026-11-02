"""
Python Authenticator - Main Application Module

This module implements the main GUI application for managing TOTP-based
two-factor authentication codes, similar to Google Authenticator.

Author: Codeplay
Date: June 2025
License: See LICENSE file
Python Version: 3.8+

Dependencies:
    - tkinter: GUI framework
    - keyboard: Global hotkey support (optional)
    - pystray: System tray integration (optional)
"""

import queue
import threading
import time
from typing import Dict, List

import tkinter as tk
from tkinter import messagebox, ttk

from database import Database
from totp_generator import TOTPGenerator
from token_widget import TokenWidget
from add_account_dialog import AddAccountDialog
from config_manager import ConfigManager
from theme import PALETTES, apply_title_bar, resolve_theme
from ui_components import action_button, icon_art, icon_image, icon_label, scaled

try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False


class AuthenticatorApp:
    """
    Main application class for Python Authenticator.
    
    This class manages the entire lifecycle of the application including:
    - GUI initialization and management
    - TOTP token generation and display
    - Database operations for account storage
    - System tray integration
    - Global hotkey registration
    
    Attributes:
        root (tk.Tk): Main application window
        config_manager (ConfigManager): Application configuration handler
        database (Database): Database interface for account storage
        totp_generator (TOTPGenerator): TOTP token generation engine
        theme_name (str): Active palette name, "light" or "dark"
        colors (Dict[str, str]): Active color palette
        token_widgets (List[tk.Frame]): Widgets currently shown in the token list
        add_dialog (Optional[AddAccountDialog]): Open add account dialog, if any
        ui_actions (queue.Queue): Actions queued by the hotkey and tray threads
        tray_icon (Optional[pystray.Icon]): System tray icon instance
        tray_thread (Optional[threading.Thread]): System tray thread
        keyboard_module: Reference to keyboard module for hotkey cleanup
        registered_hotkeys (Dict[str, str]): Registered hotkey per action name
        
    Thread Safety:
        Hotkey and tray callbacks run outside the Tk thread, so they only
        put actions in ui_actions. process_ui_actions() runs them on the
        Tk main loop.
    """
    
    def __init__(self) -> None:
        """
        Initialize the authenticator application.
        
        Sets up all necessary components including GUI, database connection,
        configuration management, and optional features like system tray
        and global hotkeys.
        
        Raises:
            Exception: If critical components fail to initialize
        """
        self.root = tk.Tk()
        
        self.config_manager = ConfigManager()
        self.database = Database()
        self.totp_generator = TOTPGenerator()
        self.theme_name = resolve_theme(self.config_manager.get('ui.theme', 'system'))
        self.colors = PALETTES[self.theme_name]
        self.style = ttk.Style(self.root)
        
        self.token_widgets: List[tk.Frame] = []
        self.add_dialog = None
        self.status_reset_job = None
        self.closing = False
        
        self.ui_actions = queue.Queue()
        self.tray_icon = None
        self.tray_thread = None
        
        self.keyboard_module = None
        self.registered_hotkeys: Dict[str, str] = {}
        self.hotkeys_armed = True
        
        self.setup_styles()
        self.setup_ui()
        self.setup_hotkeys()
        self.setup_tray()
        self.load_accounts()
        self.process_ui_actions()
        self.refresh_tokens_loop()
    
    def setup_ui(self) -> None:
        """Configure the main user interface.
        
        Sets up the main window with:
        - Window properties (title, size, colors)
        - Header section with branding and the light/dark theme toggle
        - Add account button
        - Scrollable token container
        - Status bar with hotkey information
        
        Design follows Material Design principles with Google-like aesthetics.
        """
        self.root.title("Python Authenticator")
        width = min(scaled(self.root, 440), self.root.winfo_screenwidth() - 40)
        height = min(scaled(self.root, 740), self.root.winfo_screenheight() - 100)
        self.root.geometry(f'{width}x{height}')
        self.root.minsize(min(width, scaled(self.root, 380)), min(height, scaled(self.root, 500)))
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.build_ui()

    def build_ui(self) -> None:
        colors = self.colors
        self.root.configure(bg=colors['bg'])
        self.window_icon = icon_image(self.root, 'shield', colors['accent'], size=32)
        self.root.iconphoto(True, self.window_icon)
        self.main_frame = tk.Frame(self.root, bg=colors['bg'])
        self.main_frame.pack(fill='both', expand=True, padx=20, pady=20)

        header = tk.Frame(self.main_frame, bg=colors['bg'])
        header.pack(fill='x', pady=(0, 24))
        self.theme_btn = action_button(
            header, colors, command=self.toggle_theme,
            icon='sun' if self.theme_name == 'dark' else 'moon',
            variant='ghost', background=colors['bg'], compact=True,
            hint='Usar tema claro' if self.theme_name == 'dark' else 'Usar tema escuro')
        self.theme_btn.pack(side='right', anchor='n')
        icon_label(header, 'shield', colors['accent'], colors['accent_soft'],
                   size=28, padx=10, pady=10).pack(side='left', padx=(0, 12))
        brand = tk.Frame(header, bg=colors['bg'])
        brand.pack(side='left', fill='x', expand=True)
        tk.Label(brand, text='PYTHON  /  2FA', font=('Segoe UI', 8, 'bold'),
                 fg=colors['text_secondary'], bg=colors['bg']).pack(anchor='w')
        tk.Label(brand, text='Authenticator', font=('Segoe UI', 19, 'bold'),
                 fg=colors['text'], bg=colors['bg']).pack(anchor='w')

        self.add_btn = action_button(
            self.main_frame, colors, text='Adicionar conta', icon='plus',
            variant='primary', command=self.add_account)
        self.add_btn.pack(fill='x', pady=(0, 24))

        section = tk.Frame(self.main_frame, bg=colors['bg'])
        section.pack(fill='x', pady=(0, 12))
        tk.Label(section, text='Suas contas', font=('Segoe UI', 11, 'bold'),
                 fg=colors['text'], bg=colors['bg']).pack(side='left')
        self.account_count = tk.Label(
            section, text='0', font=('Segoe UI', 9, 'bold'),
            fg=colors['accent'], bg=colors['accent_soft'], padx=9, pady=3)
        self.account_count.pack(side='right')

        # Reserve footer space before the expanding list (including small windows).
        footer = tk.Frame(self.main_frame, bg=colors['bg'])
        footer.pack(side='bottom', fill='x', pady=(14, 0))
        tk.Frame(footer, bg=colors['border'], height=1).pack(fill='x', pady=(0, 10))
        self.status_bar = tk.Label(
            footer, text='', font=('Segoe UI', 9), fg=colors['text_secondary'],
            bg=colors['bg'], anchor='w', justify='left')
        self.status_bar.pack(fill='x')
        footer.bind('<Configure>', lambda e: self.status_bar.configure(wraplength=max(1, e.width)))
        self.setup_scrollable_frame(self.main_frame)

    def setup_scrollable_frame(self, parent):
        """Configura área scrollável"""
        container = tk.Frame(parent, bg=self.colors['bg'])
        container.pack(fill='both', expand=True)
        
        self.canvas = tk.Canvas(
            container,
            bg=self.colors['bg'],
            highlightthickness=0,
            bd=0
        )
        
        scrollbar = ttk.Scrollbar(
            container,
            orient='vertical',
            command=self.canvas.yview,
            style='App.Vertical.TScrollbar'
        )
        
        self.scrollable_frame = tk.Frame(self.canvas, bg=self.colors['bg'])
        
        def configure_scroll(event):
            self.canvas.configure(scrollregion=self.canvas.bbox('all'))
            
        def on_mousewheel(event):
            if self.scrollable_frame.winfo_height() > self.canvas.winfo_height():
                steps = int(-event.delta / 120) or (-1 if event.delta > 0 else 1)
                self.canvas.yview_scroll(steps, "units")
            
        self.scrollable_frame.bind('<Configure>', configure_scroll)
        self.root.bind('<MouseWheel>', on_mousewheel)
        
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas_frame = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor='nw')
        
        self.canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        def configure_canvas(event):
            canvas_width = event.width
            self.canvas.itemconfig(canvas_frame, width=canvas_width)
            
        self.canvas.bind('<Configure>', configure_canvas)
    
    def setup_styles(self):
        """Aplica estilos"""
        self.root.configure(cursor='arrow')
        default_font = ('Segoe UI', 9)
        self.root.option_add('*Font', default_font)

        colors = self.colors
        self.style.theme_use('clam')
        self.style.layout('App.Vertical.TScrollbar', [
            ('Vertical.Scrollbar.trough', {
                'sticky': 'ns',
                'children': [('Vertical.Scrollbar.thumb', {'expand': '1', 'sticky': 'nswe'})]
            })
        ])
        self.style.configure(
            'App.Vertical.TScrollbar',
            background=colors['scrollbar'],
            troughcolor=colors['bg'],
            bordercolor=colors['bg'],
            lightcolor=colors['scrollbar'],
            darkcolor=colors['scrollbar'],
            arrowsize=9,
            gripcount=0
        )
        self.style.map(
            'App.Vertical.TScrollbar',
            background=[('active', colors['scrollbar_active'])],
            lightcolor=[('active', colors['scrollbar_active'])],
            darkcolor=[('active', colors['scrollbar_active'])]
        )

    def toggle_theme(self):
        if self.root.grab_current() is not None:
            return
        scroll_position = self.canvas.yview()[0]
        had_focus = self.root.focus_get() is self.theme_btn
        self.theme_name = 'light' if self.theme_name == 'dark' else 'dark'
        self.colors = PALETTES[self.theme_name]
        self.config_manager.set('ui.theme', self.theme_name)

        if self.status_reset_job:
            self.root.after_cancel(self.status_reset_job)
            self.status_reset_job = None
        self.main_frame.destroy()
        self.token_widgets.clear()

        self.setup_styles()
        self.build_ui()
        self.load_accounts()
        apply_title_bar(self.root, self.theme_name)
        self.root.update_idletasks()
        self.canvas.yview_moveto(scroll_position)
        if had_focus:
            self.theme_btn.focus_set()
        self.update_status('Tema claro' if self.theme_name == 'light' else 'Tema escuro', 'success')
    
    def setup_hotkeys(self) -> None:
        """Register the global hotkeys defined in config.json.
        
        Actions:
        - toggle_window (default: Ctrl+Shift+A): shows the window, or hides
          it when it already has focus
        - add_account (default: Ctrl+Shift+N): opens the add account dialog
        
        A hotkey set to "disabled" or left empty is not registered.
        Each hotkey fires once per key press: keyboard auto-repeat is
        ignored until a key is released.
        """
        try:
            import keyboard
        except ImportError:
            print("⚠ Módulo 'keyboard' não encontrado. Atalhos globais desabilitados.")
            print("  Instale com: pip install keyboard")
            return
    
        actions = {
            'toggle_window': self.toggle_window,
            'add_account': self.add_account,
        }
        hotkeys = self.config_manager.get_hotkeys()
    
        for name, action in actions.items():
            hotkey = hotkeys.get(name)
            if not hotkey or hotkey == 'disabled':
                continue
            try:
                keyboard.add_hotkey(hotkey, self._on_hotkey, args=(action,))
            except Exception as e:
                print(f"✗ Erro ao registrar hotkey {hotkey}: {e}")
                continue
            self.registered_hotkeys[name] = hotkey
            print(f"✓ Hotkey registrado: {hotkey} ({name})")

        if self.registered_hotkeys:
            keyboard.on_release(self._rearm_hotkeys)
            self.keyboard_module = keyboard

    def _on_hotkey(self, action):
        if self.hotkeys_armed:
            self.hotkeys_armed = False
            self.ui_actions.put(action)

    def _rearm_hotkeys(self, event):
        self.hotkeys_armed = True
    
    def cleanup_hotkeys(self):
        """Remove todos os atalhos registrados"""
        if self.keyboard_module:
            self.keyboard_module.unhook_all()
            self.keyboard_module = None
            self.registered_hotkeys.clear()

    def process_ui_actions(self):
        self.root.after(50, self.process_ui_actions)
        while not self.closing:
            try:
                action = self.ui_actions.get_nowait()
            except queue.Empty:
                return
            action()
    
    def create_tray_icon(self):
        """Use the same shield as the application header."""
        image = Image.new('RGBA', (64, 64))
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle((2, 2, 62, 62), radius=16, fill=PALETTES['light']['primary'])
        image.alpha_composite(icon_art('shield', '#ffffff', 40), (12, 12))
        return image

    def setup_tray(self):
        """Configura system tray"""
        if not TRAY_AVAILABLE or not self.config_manager.get('tray.enabled', True):
            return
        
        try:
            menu = pystray.Menu(
                pystray.MenuItem("Show", lambda: self.ui_actions.put(self.show_window), default=True),
                pystray.MenuItem("Add Account", lambda: self.ui_actions.put(self.add_account)),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Exit", lambda: self.ui_actions.put(self.quit_app))
            )
            
            icon_image = self.create_tray_icon()
            tooltip = self.config_manager.get('tray.tooltip', 'Python Authenticator')
            
            self.tray_icon = pystray.Icon(
                "PythonAuthenticator",
                icon_image,
                tooltip,
                menu
            )
            
        except Exception as e:
            print(f"Error setting up system tray: {e}")
            self.tray_icon = None
    
    def start_tray(self):
        """Inicia system tray em thread separada"""
        self.tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
        self.tray_thread.start()
    
    def on_closing(self):
        """Chamado quando usuário tenta fechar a janela"""
        if self.tray_icon and self.config_manager.get('tray.hide_on_close', True):
            self.hide_to_tray()
        elif messagebox.askyesno("Confirmar saída",
                                 "Deseja realmente sair do aplicativo?",
                                 parent=self.root):
            self.quit_app()
    
    def hide_to_tray(self):
        """Minimiza para a bandeja do sistema"""
        if self.tray_icon:
            self.root.withdraw()
            if not self.tray_thread or not self.tray_thread.is_alive():
                self.start_tray()
        else:
            self.root.iconify()

    def is_window_hidden(self):
        return self.root.state() in ('withdrawn', 'iconic')
    
    def show_window(self):
        """Mostra a janela"""
        if self.is_window_hidden():
            self.root.deiconify()
            
        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.after(100, lambda: self.root.attributes('-topmost',
                        self.config_manager.get('ui.always_on_top', False)))
        self.root.focus_force()
        self.position_window()
    
    def toggle_window(self):
        """Mostra a janela, ou a esconde se ela já estiver em foco"""
        if self.is_window_hidden() or self.root.focus_get() is None:
            self.show_window()
        else:
            self.hide_to_tray()
    
    def position_window(self, position=None):
        """Posiciona a janela conforme configuração"""
        self.root.update_idletasks()
        
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        window_width = max(self.root.minsize()[0], self.root.winfo_width())
        window_height = screen_height - 50
        
        ui_config = self.config_manager.get_ui_config()
        position = position or ui_config.get('window_position', 'right')
        margin = ui_config.get('margin', 20)
        if position == 'right':
            x = screen_width - window_width - margin
            y = margin
        elif position == 'left':
            x = margin
            y = margin
        elif position == 'center':
            x = (screen_width - window_width) // 2
            y = (screen_height - window_height) // 2
        elif position == 'top_right':
            x = screen_width - window_width - margin
            y = margin
        elif position == 'bottom_right':
            x = screen_width - window_width - margin
            y = screen_height - window_height - margin
        elif position == 'custom':
            x = ui_config.get('custom_x', 100)
            y = ui_config.get('custom_y', 100)
        else:
            x = screen_width - window_width - margin
            y = margin
        
        x = max(0, min(x, screen_width - window_width))
        y = max(0, min(y, screen_height - window_height))
        
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        if ui_config.get('always_on_top', False):
            self.root.attributes('-topmost', True)
    
    def quit_app(self):
        """Sai completamente do aplicativo"""
        if self.closing:
            return
        self.closing = True
        print("\n🔄 Encerrando aplicativo...")

        self.cleanup_hotkeys()
        if self.tray_thread and self.tray_thread.is_alive():
            self.tray_icon.stop()
            self.tray_thread.join(timeout=2)
        self.root.destroy()
        
        print("✓ Aplicativo encerrado")
    
    def load_accounts(self):
        """Load accounts and render a useful empty state."""
        self.clear_tokens()
        accounts = self.database.get_all_accounts()
        self.account_count.configure(text=str(len(accounts)))
        if not accounts:
            colors = self.colors
            empty = tk.Frame(self.scrollable_frame, bg=colors['surface'],
                             highlightthickness=1, highlightbackground=colors['border'])
            empty.pack(fill='x', pady=2)
            icon_label(empty, 'lock', colors['accent'], colors['surface'], size=42).pack(pady=(28, 14))
            tk.Label(empty, text='Sua próxima camada de proteção',
                     font=('Segoe UI', 12, 'bold'), fg=colors['text'],
                     bg=colors['surface'], wraplength=270).pack(padx=16)
            tk.Label(empty, text='Adicione sua primeira conta para gerar códigos de verificação aqui.',
                     font=('Segoe UI', 10), fg=colors['text_secondary'],
                     bg=colors['surface'], wraplength=260, justify='center').pack(padx=16, pady=(10, 28))
            self.token_widgets.append(empty)
        else:
            for i, account in enumerate(accounts):
                self.create_token_widget(account, i == 0)
        self.update_status(f"{len(accounts)} conta(s)", 'success')

    def create_token_widget(self, account_data, is_first=False):
        """Cria widget para token"""
        margin_top = 0 if is_first else 12
        
        widget = TokenWidget(
            self.scrollable_frame,
            account_data,
            self.totp_generator,
            self.delete_account,
            self.theme_name
        )
        widget.pack(fill='x', pady=(margin_top, 0))
        self.token_widgets.append(widget)
    
    def clear_tokens(self):
        """Remove todos os widgets"""
        for widget in self.token_widgets:
            widget.destroy()
        self.token_widgets.clear()
    
    def add_account(self):
        """Abre diálogo para adicionar conta"""
        if self.is_window_hidden():
            self.show_window()

        if self.add_dialog:
            self.add_dialog.bring_to_front()
            return
        
        self.add_dialog = AddAccountDialog(self.root, self.totp_generator, self.theme_name)
        try:
            result = self.add_dialog.show()
        finally:
            self.add_dialog = None
        
        if not result or self.closing:
            return

        try:
            self.database.add_account(
                result['name'],
                result['secret'],
                result['issuer']
            )
        except Exception as e:
            messagebox.showerror("Error", f"Error adding account: {e}", parent=self.root)
            self.update_status("Error adding account", "error")
            return
        
        self.load_accounts()
        self.update_status("Conta adicionada", "success")
    
    def delete_account(self, account_id):
        """Remove conta"""
        try:
            accounts = self.database.get_all_accounts()
            if not any(acc[0] == account_id for acc in accounts):
                messagebox.showwarning("Aviso", "Conta não encontrada.")
                self.load_accounts()
                return
            
            self.database.delete_account(account_id)
            self.load_accounts()
            self.update_status("Conta removida", "success")
        except Exception as e:
            error_msg = f"Error removing account: {str(e)}"
            print(f"✗ {error_msg}")
            messagebox.showerror("Error", error_msg)
            self.update_status("Error removing account", "error")
    
    def refresh_tokens(self):
        """Atualiza todos os tokens"""
        for widget in self.token_widgets:
            if isinstance(widget, TokenWidget):
                widget.update_token()
            
    def refresh_tokens_loop(self):
        self.refresh_tokens()
        delay_ms = 1000 - int(time.time() * 1000) % 1000
        self.root.after(delay_ms, self.refresh_tokens_loop)

    def ready_message(self):
        toggle_hotkey = self.registered_hotkeys.get('toggle_window')
        if toggle_hotkey:
            return f"{toggle_hotkey.upper()}  ·  Mostrar / ocultar"
        return "Pronto para gerar seus códigos"

    def show_ready_status(self):
        self.status_reset_job = None
        self.status_bar.configure(text=self.ready_message(), fg=self.colors['text_secondary'])
    
    def update_status(self, message, status_type="info"):
        """Atualiza status com cores"""
        colors = {
            "success": self.colors['success'],
            "error": self.colors['error'],
            "info": self.colors['text_secondary']
        }
        
        self.status_bar.configure(text=message, fg=colors.get(status_type, self.colors['text_secondary']))
        
        if self.status_reset_job:
            self.root.after_cancel(self.status_reset_job)
            self.status_reset_job = None

        if status_type != "error":
            self.status_reset_job = self.root.after(3000, self.show_ready_status)
    
    def run(self):
        """Executa o app"""
        self.position_window()
        apply_title_bar(self.root, self.theme_name)
        self.root.mainloop()
