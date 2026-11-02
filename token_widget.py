"""
Token Widget Module for Python Authenticator

This module implements the individual token display widget that shows:
- Account name and issuer
- Current TOTP code (updates every 30 seconds)
- Progress bar for token validity
- Copy, recover, and delete actions

Design follows Material Design principles with card-based layout.

Author: Codeplay
Date: June 2025
"""

from typing import Callable, Tuple

import tkinter as tk
from tkinter import messagebox

from theme import PALETTES, apply_title_bar
from ui_components import action_button, icon_label, ElidedLabel


class TokenWidget(tk.Frame):
    """
    Individual TOTP token display card widget.
    
    Displays a single 2FA account with:
    - Account name and issuer (service provider)
    - Current 6-digit TOTP code (formatted as "123 456")
    - Visual progress bar showing token validity
    - Time remaining until next token
    - Copy button for quick clipboard access
    - Recover button to retrieve original secret key
    - Delete button with confirmation dialog
    
    The widget updates automatically every second to refresh:
    - Token value (every 30 seconds)
    - Progress bar
    - Time remaining counter
    
    Attributes:
        account_id (int): Database ID of the account
        name (str): Account name/identifier
        secret (str): Decrypted TOTP secret key
        issuer (str): Service provider name
        totp_generator (TOTPGenerator): Token generation engine
        on_delete_callback (Callable): Function to call when account deleted
        theme_name (str): Palette name, "light" or "dark"
        colors (Dict[str, str]): Color palette used by the card
        
    UI Components:
        card (Frame): Main card container with surface background
        token_label (Label): Displays the 6-digit TOTP code
        progress_bar (Frame): Visual indicator of token validity
        time_label (Label): Shows seconds remaining
        copy_btn (Button): Copies token to clipboard
        recover_btn (Button): Retrieves original secret key
        delete_btn (Button): Deletes account with confirmation
    """
    
    def __init__(
        self, 
        parent: tk.Widget,
        account_data: Tuple[int, str, str, str],
        totp_generator,
        on_delete_callback: Callable[[int], None],
        theme_name: str
    ) -> None:
        """
        Initialize token display widget.
        
        Args:
            parent: Parent tkinter widget
            account_data: Tuple of (id, name, secret, issuer)
            totp_generator: TOTPGenerator instance for token creation
            on_delete_callback: Function to call when account is deleted
            theme_name: Palette name, "light" or "dark"
        """
        self.theme_name = theme_name
        self.colors = PALETTES[theme_name]
        super().__init__(parent, bg=self.colors['bg'])

        self.account_id, self.name, self.secret, self.issuer = account_data
        self.totp_generator = totp_generator
        self.on_delete_callback = on_delete_callback

        self.feedback_job = None
        self.setup_ui()
        self.update_token()
    
    def setup_ui(self):
        colors = self.colors
        self.card = tk.Frame(self, bg=colors['surface'], highlightthickness=1,
                             highlightbackground=colors['border'])
        self.card.pack(fill='x', padx=1, pady=1)
        content = tk.Frame(self.card, bg=colors['surface'])
        content.pack(fill='x', padx=16, pady=16)

        header = tk.Frame(content, bg=colors['surface'])
        header.pack(fill='x', pady=(0, 16))
        header.columnconfigure(1, weight=1, minsize=0)
        display_name = self.issuer or self.name or 'Conta'
        tk.Label(header, text=display_name[:1].upper(), font=('Segoe UI', 13, 'bold'),
                 fg=colors['accent'], bg=colors['accent_soft'], width=3, pady=6).grid(
                     row=0, column=0, rowspan=2, padx=(0, 10), sticky='n')
        ElidedLabel(header, display_name, colors, font=('Segoe UI', 11, 'bold'),
                    fg=colors['text'], bg=colors['surface'], width=1).grid(row=0, column=1, sticky='ew')
        ElidedLabel(header, self.name if self.issuer else 'Autenticação em duas etapas',
                    colors, font=('Segoe UI', 9), fg=colors['text_secondary'],
                    bg=colors['surface'], width=1).grid(row=1, column=1, sticky='ew')

        code_row = tk.Frame(content, bg=colors['surface'])
        code_row.pack(fill='x', pady=(0, 12))
        self.copy_btn = action_button(code_row, colors, text='Copiar', icon='copy',
                                      command=self.copy_token, compact=True, hint='Copiar código de verificação')
        self.copy_btn.pack(side='right')
        self.token_label = tk.Label(
            code_row, text='000 000', font=('Consolas', 27, 'bold'),
            fg=colors['accent'], bg=colors['surface'], cursor='hand2', anchor='w')
        self.token_label.pack(side='left', fill='x', expand=True)
        self.token_label.bind('<Button-1>', lambda e: self.copy_token())

        self.progress_bg = tk.Frame(content, bg=colors['track'], height=4)
        self.progress_bg.pack(fill='x', pady=(0, 10))
        self.progress_bar = tk.Frame(self.progress_bg, bg=colors['accent'])
        self.progress_bar.place(x=0, y=0, relheight=1, relwidth=1)
        timing = tk.Frame(content, bg=colors['surface'])
        timing.pack(fill='x')
        self.time_label = tk.Label(timing, text='', font=('Segoe UI', 9),
                                   fg=colors['text_secondary'], bg=colors['surface'])
        self.time_label.pack(side='left')
        self.status_label = tk.Label(timing, text='Ativo', font=('Segoe UI', 9),
                                     fg=colors['success'], bg=colors['surface'])
        self.status_label.pack(side='right')

        tk.Frame(content, bg=colors['border'], height=1).pack(fill='x', pady=(12, 8))
        actions = tk.Frame(content, bg=colors['surface'])
        actions.pack(fill='x')
        tk.Label(actions, text='TOTP', font=('Segoe UI', 8, 'bold'),
                 fg=colors['text_muted'], bg=colors['surface']).pack(side='left')
        self.delete_btn = action_button(
            actions, colors, icon='trash', command=self.confirm_delete,
            variant='danger_ghost', compact=True, hint='Excluir conta')
        self.delete_btn.pack(side='right')
        self.recover_btn = action_button(
            actions, colors, icon='key', command=self.copy_original_secret,
            variant='ghost', compact=True, hint='Copiar chave secreta original')
        self.recover_btn.pack(side='right', padx=(0, 6))

    def show_feedback(self, message):
        if self.feedback_job:
            self.after_cancel(self.feedback_job)
        self.status_label.configure(text=message, fg=self.colors['success'])
        self.feedback_job = self.after(2000, self.clear_feedback)

    def clear_feedback(self):
        self.feedback_job = None
        self.update_token()

    def destroy(self):
        if self.feedback_job:
            self.after_cancel(self.feedback_job)
            self.feedback_job = None
        super().destroy()

    def copy_original_secret(self):
        """Copia a chave OTP original para o clipboard"""
        try:
            if not self.winfo_exists():
                return

            msg = (
                "Você está prestes a copiar a chave secreta original desta conta.\n\n"
                "ATENÇÃO: Esta chave dá acesso completo à sua autenticação de dois fatores!\n\n"
                "Apenas copie se você sabe o que está fazendo.\n\n"
                "Deseja continuar?"
            )

            if not messagebox.askyesno("Aviso de Segurança", msg, parent=self):
                return

            self.clipboard_clear()
            self.clipboard_append(self.secret)
            self.update()

            self.show_feedback("Chave copiada")

            messagebox.showinfo(
                "Sucesso",
                "Chave secreta copiada para a área de transferência!\n\n"
                "Guarde-a em um local seguro.",
                parent=self
            )

        except tk.TclError as e:
            print(f"Erro TclError ao copiar chave: {e}")

    def update_token(self):
        """Atualiza o código TOTP e UI"""
        try:
            if not self.winfo_exists():
                return
            
            token = self.totp_generator.generate_token(self.secret)
            
            if token != "ERROR" and len(token) == 6 and token.isdigit():
                formatted_token = f"{token[:3]} {token[3:]}"
                self.token_label.configure(text=formatted_token, fg=self.colors['accent'])
                if not self.feedback_job:
                    self.status_label.configure(text="Ativo", fg=self.colors['success'])
            else:
                self.token_label.configure(text="ERROR", fg=self.colors['error'])
                self.status_label.configure(text="Erro no código", fg=self.colors['error'])
                print(f"Token inválido gerado para {self.name}: {token}")
            
            period = self.totp_generator.period
            remaining = self.totp_generator.get_time_remaining()
            progress = max(0, min(1, remaining / period))
            self.progress_bar.place_configure(relwidth=progress)

            if remaining <= 5:
                self.progress_bar.configure(bg=self.colors['warning'])
                self.time_label.configure(fg=self.colors['warning'])
            else:
                self.progress_bar.configure(bg=self.colors['accent'])
                self.time_label.configure(fg=self.colors['text_secondary'])
            
            self.time_label.configure(text=f"Renova em {remaining}s")
            
        except Exception as e:
            self.token_label.configure(text="ERROR", fg=self.colors['error'])
            self.status_label.configure(text="Erro no código", fg=self.colors['error'])
            print(f"Erro ao atualizar token: {e}")
    
    def copy_token(self):
        """Copia token para clipboard"""
        try:
            if not self.winfo_exists():
                return
            
            token = self.totp_generator.generate_token(self.secret)
            
            if token != "ERROR" and len(token) == 6 and token.isdigit():
                self.clipboard_clear()
                self.clipboard_append(token)
                self.update()
                
                self.show_feedback("Código copiado")

            else:
                messagebox.showwarning(
                    "Token Inválido", 
                    "Não foi possível gerar um token válido.\nVerifique a chave secreta.",
                    parent=self
                )
                return
                
        except tk.TclError as e:
            print(f"Erro TclError ao copiar token: {e}")
        except Exception as e:
            print(f"Erro ao copiar token: {e}")
            messagebox.showerror("Erro", f"Erro ao copiar token: {str(e)}", parent=self)
    
    def confirm_delete(self):
        """Keep the destructive action explicit and all controls visible."""
        if not self.winfo_exists():
            return
        colors = self.colors
        dialog = tk.Toplevel(self)
        dialog.title('Excluir conta')
        dialog.resizable(False, False)
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        dialog.configure(bg=colors['surface'])
        content = tk.Frame(dialog, bg=colors['surface'], padx=24, pady=24)
        content.pack(fill='both', expand=True)
        icon_label(content, 'trash', colors['error'], colors['error_soft'],
                   size=28, padx=12, pady=12).pack(pady=(0, 16))
        tk.Label(content, text='Excluir esta conta?', font=('Segoe UI', 15, 'bold'),
                 fg=colors['text'], bg=colors['surface']).pack(pady=(0, 10))
        name = self.issuer or self.name
        display_name = name if len(name) <= 100 else name[:97] + '…'
        tk.Label(content, text=f'A conta “{display_name}” será removida deste aplicativo.',
                 font=('Segoe UI', 10), fg=colors['text_secondary'], bg=colors['surface'],
                 wraplength=300, justify='center').pack(pady=(0, 22))
        buttons = tk.Frame(content, bg=colors['surface'])
        buttons.pack(fill='x')

        def confirm():
            dialog.destroy()
            self.on_delete_callback(self.account_id)

        cancel_btn = action_button(buttons, colors, text='Cancelar', command=dialog.destroy)
        cancel_btn.pack(side='left', expand=True, fill='x', padx=(0, 10))
        action_button(buttons, colors, text='Excluir', variant='danger',
                      command=confirm).pack(side='right', expand=True, fill='x')
        dialog.bind('<Escape>', lambda e: dialog.destroy())
        # Enter activates the focused button; the initial focus is Cancel.
        dialog.update_idletasks()
        width = max(360, dialog.winfo_reqwidth())
        height = dialog.winfo_reqheight()
        x = max(0, self.winfo_rootx() + (self.winfo_width() - width) // 2)
        y = max(0, (dialog.winfo_screenheight() - height) // 2)
        dialog.geometry(f'{width}x{height}+{x}+{y}')
        apply_title_bar(dialog, self.theme_name)
        cancel_btn.focus_force()
