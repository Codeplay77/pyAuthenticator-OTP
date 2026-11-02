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
        
    UI Components:
        card (Frame): Main card container with white background
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
        on_delete_callback: Callable[[int], None]
    ) -> None:
        """
        Initialize token display widget.
        
        Args:
            parent: Parent tkinter widget
            account_data: Tuple of (id, name, secret, issuer)
            totp_generator: TOTPGenerator instance for token creation
            on_delete_callback: Function to call when account is deleted
        """
        super().__init__(parent, bg='#f0f2f5')

        self.account_id, self.name, self.secret, self.issuer = account_data
        self.totp_generator = totp_generator
        self.on_delete_callback = on_delete_callback

        self.setup_ui()
        self.update_token()
    
    def setup_ui(self):
        """Interface moderna do token"""
        self.card = tk.Frame(
            self,
            bg='white',
            relief='flat',
            bd=0
        )
        self.card.pack(fill='x', padx=2, pady=2)
        
        shadow = tk.Frame(self, bg='#e0e0e0', height=2)
        shadow.pack(fill='x', padx=4)
        
        content_frame = tk.Frame(self.card, bg='white')
        content_frame.pack(fill='x', padx=20, pady=20)
        
        header_frame = tk.Frame(content_frame, bg='white')
        header_frame.pack(fill='x', pady=(0, 15))
        
        display_name = f"{self.issuer}" if self.issuer else "Conta"
        account_name = self.name if self.name else "Sem nome"
        
        if self.issuer:
            issuer_label = tk.Label(
                header_frame,
                text=display_name,
                font=('Segoe UI', 11, 'bold'),
                fg='#202124',
                bg='white'
            )
            issuer_label.pack(anchor='w')
            
            name_label = tk.Label(
                header_frame,
                text=account_name,
                font=('Segoe UI', 9),
                fg='#5f6368',
                bg='white'
            )
            name_label.pack(anchor='w')
        else:
            name_label = tk.Label(
                header_frame,
                text=account_name,
                font=('Segoe UI', 11, 'bold'),
                fg='#202124',
                bg='white'
            )
            name_label.pack(anchor='w')
        
        self.recover_btn = tk.Button(
            header_frame,
            text="🔑",
            font=('Segoe UI', 12),
            fg='#9aa0a6',
            bg='white',
            activebackground='#e8f0fe',
            activeforeground='#1a73e8',
            relief='flat',
            bd=0,
            width=2,
            height=1,
            cursor='hand2',
            command=self.copy_original_secret
        )
        self.recover_btn.place(relx=0.85, rely=0.5, anchor='e')
        
        def on_recover_enter(e):
            self.recover_btn.configure(bg='#e8f0fe', fg='#1a73e8')
        def on_recover_leave(e):
            self.recover_btn.configure(bg='white', fg='#9aa0a6')
            
        self.recover_btn.bind('<Enter>', on_recover_enter)
        self.recover_btn.bind('<Leave>', on_recover_leave)
        
        self.delete_btn = tk.Button(
            header_frame,
            text="×",
            font=('Segoe UI', 16, 'bold'),
            fg='#9aa0a6',
            bg='white',
            activebackground='#fce8e6',
            activeforeground='#d93025',
            relief='flat',
            bd=0,
            width=2,
            height=1,
            cursor='hand2',
            command=self.confirm_delete
        )
        self.delete_btn.place(relx=1.0, rely=0.5, anchor='e')
        
        def on_delete_enter(e):
            self.delete_btn.configure(bg='#fce8e6', fg='#d93025')
        def on_delete_leave(e):
            self.delete_btn.configure(bg='white', fg='#9aa0a6')
            
        self.delete_btn.bind('<Enter>', on_delete_enter)
        self.delete_btn.bind('<Leave>', on_delete_leave)
        
        token_frame = tk.Frame(content_frame, bg='white')
        token_frame.pack(fill='x', pady=(0, 15))
        
        self.token_label = tk.Label(
            token_frame,
            text="000 000",
            font=('JetBrains Mono', 28, 'bold'),
            fg='#1a73e8',
            bg='white',
            cursor='hand2'
        )
        self.token_label.pack(side='left')
        
        self.token_label.bind('<Button-1>', lambda e: self.copy_token())
        
        self.copy_btn = tk.Button(
            token_frame,
            text="📋",
            font=('Segoe UI', 14),
            fg='#5f6368',
            bg='white',
            activebackground='#e8f0fe',
            activeforeground='#1a73e8',
            relief='flat',
            bd=0,
            width=3,
            height=1,
            cursor='hand2',
            command=self.copy_token
        )
        self.copy_btn.pack(side='right', padx=(10, 0))
        
        def on_copy_enter(e):
            self.copy_btn.configure(bg='#e8f0fe', fg='#1a73e8')
        def on_copy_leave(e):
            self.copy_btn.configure(bg='white', fg='#5f6368')
            
        self.copy_btn.bind('<Enter>', on_copy_enter)
        self.copy_btn.bind('<Leave>', on_copy_leave)
        
        progress_container = tk.Frame(content_frame, bg='white', height=6)
        progress_container.pack(fill='x', pady=(0, 10))
        progress_container.pack_propagate(False)
        
        self.progress_bg = tk.Frame(progress_container, bg='#e8eaed', height=4)
        self.progress_bg.pack(fill='x', pady=1)
        
        self.progress_bar = tk.Frame(self.progress_bg, bg='#1a73e8', height=4)
        self.progress_bar.pack(side='left', fill='y')
        
        time_frame = tk.Frame(content_frame, bg='white')
        time_frame.pack(fill='x')
        
        self.time_label = tk.Label(
            time_frame,
            text="30s",
            font=('Segoe UI', 9),
            fg='#5f6368',
            bg='white'
        )
        self.time_label.pack(side='left')
        
        self.status_label = tk.Label(
            time_frame,
            text="✓ Ativo",
            font=('Segoe UI', 9),
            fg='#137333',
            bg='white'
        )
        self.status_label.pack(side='right')
    
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

            original_text = self.recover_btn['text']
            original_color = self.recover_btn['fg']

            self.recover_btn.configure(text="✓", fg='#137333')
            self.after(1500, lambda: self.recover_btn.configure(
                text=original_text,
                fg=original_color
            ))

            self.status_label.configure(text="🔑 Chave copiada", fg='#137333')
            self.after(2000, lambda: self.status_label.configure(
                text="✓ Ativo",
                fg='#137333'
            ))

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
                self.token_label.configure(text=formatted_token, fg='#1a73e8')
                self.status_label.configure(text="✓ Ativo", fg='#137333')
            else:
                self.token_label.configure(text="ERROR", fg='#d93025')
                self.status_label.configure(text="✗ Erro", fg='#d93025')
                print(f"Token inválido gerado para {self.name}: {token}")
            
            period = self.totp_generator.period
            remaining = self.totp_generator.get_time_remaining()
            progress = (period - remaining) / period
            
            try:
                container_width = self.progress_bg.winfo_width()
                if container_width > 1: 
                    bar_width = int(container_width * progress)
                    self.progress_bar.configure(width=bar_width)
            except:
                pass
            
            if remaining <= 5:
                self.progress_bar.configure(bg='#ea4335')
                self.time_label.configure(fg='#ea4335')
            else:
                self.progress_bar.configure(bg='#1a73e8')
                self.time_label.configure(fg='#5f6368')
            
            self.time_label.configure(text=f"{remaining}s")
            
        except Exception as e:
            self.token_label.configure(text="ERROR", fg='#d93025')
            self.status_label.configure(text="✗ Erro", fg='#d93025')
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
                
                original_text = self.copy_btn['text']
                original_color = self.copy_btn['fg']
                
                self.copy_btn.configure(text="✓", fg='#137333')
                self.after(1500, lambda: self.copy_btn.configure(
                    text=original_text, 
                    fg=original_color
                ))
                
                self.status_label.configure(text="📋 Copiado", fg='#137333')
                self.after(2000, lambda: self.status_label.configure(
                    text="✓ Ativo", 
                    fg='#137333'
                ))
                
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
        """Confirma exclusão com diálogo moderno"""
        if not self.winfo_exists():
            return
        
        dialog_width = 350
        dialog_height = 250

        dialog = tk.Toplevel(self)
        dialog.title("Confirmar exclusão")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        dialog.configure(bg='white')

        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog_width // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog_height // 2)
        dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
        
        content = tk.Frame(dialog, bg='white', padx=30, pady=30)
        content.pack(fill='both', expand=True)
        
        icon_label = tk.Label(
            content,
            text="⚠️",
            font=('Segoe UI', 24),
            bg='white'
        )
        icon_label.pack(pady=(0, 15))
        
        title_label = tk.Label(
            content,
            text="Excluir conta?",
            font=('Segoe UI', 14, 'bold'),
            fg='#202124',
            bg='white'
        )
        title_label.pack(pady=(0, 10))
        
        display_name = self.issuer if self.issuer else self.name
        msg_label = tk.Label(
            content,
            text=f"A conta '{display_name}' será removida\npermanentemente.",
            font=('Segoe UI', 10),
            fg='#5f6368',
            bg='white',
            justify='center'
        )
        msg_label.pack(pady=(0, 20))
        
        button_frame = tk.Frame(content, bg='white')
        button_frame.pack(fill='x')
        
        def cancel():
            dialog.destroy()
            
        def confirm():
            dialog.destroy()
            self.on_delete_callback(self.account_id)
        
        cancel_btn = tk.Button(
            button_frame,
            text="Cancelar",
            font=('Segoe UI', 10),
            fg='#1a73e8',
            bg='white',
            activebackground='#e8f0fe',
            activeforeground='#1a73e8',
            relief='flat',
            bd=1,
            padx=20,
            pady=8,
            cursor='hand2',
            command=cancel
        )
        cancel_btn.pack(side='right', padx=(10, 0))
        
        delete_btn = tk.Button(
            button_frame,
            text="Excluir",
            font=('Segoe UI', 10, 'bold'),
            fg='white',
            bg='#d93025',
            activebackground='#b52d20',
            activeforeground='white',
            relief='flat',
            bd=0,
            padx=20,
            pady=8,
            cursor='hand2',
            command=confirm
        )
        delete_btn.pack(side='right')

        dialog.bind('<Escape>', lambda e: cancel())
        dialog.bind('<Return>', lambda e: confirm())
        cancel_btn.focus_force()