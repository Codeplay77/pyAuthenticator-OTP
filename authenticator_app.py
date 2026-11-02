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
from tkinter import messagebox

from database import Database
from totp_generator import TOTPGenerator
from token_widget import TokenWidget
from add_account_dialog import AddAccountDialog
from config_manager import ConfigManager

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
        
        self.setup_ui()
        self.setup_styles()
        self.setup_hotkeys()
        self.setup_tray()
        self.load_accounts()
        self.process_ui_actions()
        self.refresh_tokens_loop()
    
    def setup_ui(self) -> None:
        """Configure the main user interface.
        
        Sets up the main window with:
        - Window properties (title, size, colors)
        - Header section with branding
        - Add account button
        - Scrollable token container
        - Status bar with hotkey information
        
        Design follows Material Design principles with Google-like aesthetics.
        """
        self.root.title("Python Authenticator")
        self.root.geometry("420x700")
        self.root.minsize(380, 500)
        self.root.configure(bg='#f0f2f5')
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        main_frame = tk.Frame(self.root, bg='#f0f2f5')
        main_frame.pack(fill='both', expand=True, padx=15, pady=15)
        header_frame = tk.Frame(main_frame, bg='#f0f2f5', height=80)
        header_frame.pack(fill='x', pady=(0, 20))
        header_frame.pack_propagate(False)
        title_label = tk.Label(
            header_frame,
            text="Python Authenticator",
            font=('Segoe UI', 22, 'bold'),
            fg='#1a73e8',
            bg='#f0f2f5'
        )
        title_label.pack(pady=(15, 5))
        
        subtitle_label = tk.Label(
            header_frame,
            text="TOTP Authentication Manager",
            font=('Segoe UI', 10),
            fg='#5f6368',
            bg='#f0f2f5'
        )
        subtitle_label.pack()
        add_button_frame = tk.Frame(main_frame, bg='#f0f2f5')
        add_button_frame.pack(fill='x', pady=(0, 20))
        
        self.add_btn = tk.Button(
            add_button_frame,
            text="Add Account",
            font=('Segoe UI', 11, 'bold'),
            fg='white',
            bg='#1a73e8',
            activebackground='#1557b0',
            activeforeground='white',
            relief='flat',
            bd=0,
            pady=12,
            cursor='hand2',
            command=self.add_account
        )
        self.add_btn.pack(fill='x')
        self.setup_scrollable_frame(main_frame)
        status_frame = tk.Frame(main_frame, bg='#f0f2f5', height=30)
        status_frame.pack(side='bottom', fill='x', pady=(15, 0))
        status_frame.pack_propagate(False)
        
        self.status_bar = tk.Label(
            status_frame,
            text="",
            font=('Segoe UI', 9),
            fg='#5f6368',
            bg='#f0f2f5'
        )
        self.status_bar.pack(pady=8)
    
    def setup_scrollable_frame(self, parent):
        """Configura área scrollável"""
        container = tk.Frame(parent, bg='#f0f2f5')
        container.pack(fill='both', expand=True)
        
        self.canvas = tk.Canvas(
            container,
            bg='#f0f2f5',
            highlightthickness=0,
            bd=0
        )
        
        scrollbar = tk.Scrollbar(
            container,
            orient='vertical',
            command=self.canvas.yview,
            bg='#dadce0',
            troughcolor='#e8eaed',
            width=12
        )
        
        self.scrollable_frame = tk.Frame(self.canvas, bg='#f0f2f5')
        
        def configure_scroll(event):
            self.canvas.configure(scrollregion=self.canvas.bbox('all'))
            
        def on_mousewheel(event):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            
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
        """Cria ícone para a bandeja do sistema"""
        width = height = 64
        image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        margin = 8
        draw.ellipse(
            [margin, margin, width-margin, height-margin],
            fill='#1a73e8',
            outline='#1557b0',
            width=2
        )
        
        text = "2FA"
        bbox = draw.textbbox((0, 0), text, font=None)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (width - text_width) // 2
        y = (height - text_height) // 2 - 2
        
        draw.text((x, y), text, fill='white')
        
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
        
        window_width = 420
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
        """Carrega contas"""
        self.clear_tokens()
        
        accounts = self.database.get_all_accounts()
        
        if not accounts:
            empty_frame = tk.Frame(self.scrollable_frame, bg='#f0f2f5')
            empty_frame.pack(expand=True, fill='both', pady=50)
            
            icon_label = tk.Label(
                empty_frame,
                text="🔒",
                font=('Segoe UI', 48),
                bg='#f0f2f5',
                fg='#dadce0'
            )
            icon_label.pack(pady=(0, 20))
            
            title_label = tk.Label(
                empty_frame,
                text="No accounts added",
                font=('Segoe UI', 16, 'bold'),
                fg='#5f6368',
                bg='#f0f2f5'
            )
            title_label.pack(pady=(0, 10))
            
            subtitle_label = tk.Label(
                empty_frame,
                text="Click 'Add Account' to start\nprotecting your accounts with 2FA",
                font=('Segoe UI', 11),
                fg='#9aa0a6',
                bg='#f0f2f5',
                justify='center'
            )
            subtitle_label.pack()
            
            self.token_widgets.append(empty_frame)
        else:
            for i, account in enumerate(accounts):
                self.create_token_widget(account, i == 0)
        
        self.update_status(f"{len(accounts)} account(s)", "success")
    
    def create_token_widget(self, account_data, is_first=False):
        """Cria widget para token"""
        margin_top = 0 if is_first else 15
        
        widget = TokenWidget(
            self.scrollable_frame,
            account_data,
            self.totp_generator,
            self.delete_account
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
        
        self.add_dialog = AddAccountDialog(self.root, self.totp_generator)
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
        self.update_status(f"Account '{result['name']}' added", "success")
    
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
            self.update_status("Account removed", "success")
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
            return f"Ready - {toggle_hotkey.upper()} to toggle"
        return "Ready"

    def show_ready_status(self):
        self.status_reset_job = None
        self.status_bar.configure(text=self.ready_message(), fg="#5f6368")
    
    def update_status(self, message, status_type="info"):
        """Atualiza status com cores"""
        colors = {
            "success": "#137333",
            "error": "#d93025",
            "info": "#5f6368"
        }
        
        self.status_bar.configure(text=message, fg=colors.get(status_type, "#5f6368"))
        
        if self.status_reset_job:
            self.root.after_cancel(self.status_reset_job)
            self.status_reset_job = None

        if status_type != "error":
            self.status_reset_job = self.root.after(3000, self.show_ready_status)
    
    def run(self):
        """Executa o app"""
        self.position_window()
        self.root.mainloop()
