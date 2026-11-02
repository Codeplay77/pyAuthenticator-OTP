"""
Add Account Dialog Module for Python Authenticator

Provides a modal dialog for adding new 2FA accounts with:
- Account name input (required)
- Service issuer input (optional)
- Secret key input with validation (required)
- Real-time validation feedback
- Show/hide secret key toggle

Design follows Material Design with blue accent colors.

Author: Codeplay
Date: June 2025
"""

import tkinter as tk
from tkinter import messagebox


class AddAccountDialog:
    def __init__(self, parent, totp_generator):
        self.parent = parent
        self.totp_generator = totp_generator
        self.result = None
        self.setup_dialog()

    def setup_dialog(self):
        """Interface moderna do diálogo"""
        window_width = 420
        window_height = 780
        
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Adicionar conta")
        self.dialog.geometry(f"{window_width}x{window_height}")
        self.dialog.resizable(False, False)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        self.dialog.configure(bg='white')
        self.dialog.bind('<Escape>', lambda e: self.cancel())
        self.dialog.bind('<Return>', lambda e: self.add_account())
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (window_width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (window_height // 2)
        self.dialog.geometry(f"{window_width}x{window_height}+{x}+{y}")
        header = tk.Frame(self.dialog, bg='#1a73e8', height=80)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        header_content = tk.Frame(header, bg='#1a73e8')
        header_content.pack(expand=True, fill='both', padx=30, pady=20)
        
        title_label = tk.Label(
            header_content,
            text="🔐 Adicionar nova conta",
            font=('Segoe UI', 16, 'bold'),
            fg='white',
            bg='#1a73e8'
        )
        title_label.pack(anchor='w')
        
        subtitle_label = tk.Label(
            header_content,
            text="Digite as informações da sua conta 2FA",
            font=('Segoe UI', 10),
            fg='#e3f2fd',
            bg='#1a73e8'
        )
        subtitle_label.pack(anchor='w', pady=(5, 0))
        main_content = tk.Frame(self.dialog, bg='white')
        main_content.pack(fill='both', expand=True, padx=30, pady=30)
        form_container = tk.Frame(main_content, bg='white')
        form_container.pack(fill='both', expand=True, pady=(0, 20))
        
        self.setup_manual_form(form_container)
        button_frame = tk.Frame(main_content, bg='white')
        button_frame.pack(fill='x', pady=(20, 0))
        
        cancel_btn = tk.Button(
            button_frame,
            text="Cancelar",
            font=('Segoe UI', 11),
            fg='#5f6368',
            bg='white',
            activebackground='#f8f9fa',
            relief='flat',
            bd=1,
            padx=25,
            pady=10,
            cursor='hand2',
            command=self.cancel
        )
        cancel_btn.pack(side='right', padx=(10, 0))

        self.add_btn = tk.Button(
            button_frame,
            text="Adicionar conta",
            font=('Segoe UI', 11, 'bold'),
            fg='white',
            bg='#1a73e8',
            activebackground='#1557b0',
            relief='flat',
            bd=0,
            padx=25,
            pady=10,
            cursor='hand2',
            command=self.add_account
        )
        self.add_btn.pack(side='right')
    
    def setup_manual_form(self, parent):
        """Formulário direto sem tabs"""
        form_frame = tk.Frame(parent, bg='white')
        form_frame.pack(fill='both', expand=True)
        
        tk.Label(
            form_frame,
            text="Nome da conta",
            font=('Segoe UI', 10, 'bold'),
            fg='#202124',
            bg='white'
        ).pack(anchor='w', pady=(0, 8))
        
        self.name_entry = tk.Entry(
            form_frame,
            font=('Segoe UI', 11),
            bg='#f8f9fa',
            fg='#202124',
            relief='flat',
            bd=8,
            highlightthickness=1,
            highlightcolor='#1a73e8',
            highlightbackground='#e0e0e0'
        )
        self.name_entry.pack(fill='x', pady=(0, 20), ipady=8)
        
        self.dialog.after(100, self.name_entry.focus_force)
        
        tk.Label(
            form_frame,
            text="Emissor (opcional)",
            font=('Segoe UI', 10, 'bold'),
            fg='#202124',
            bg='white'
        ).pack(anchor='w', pady=(0, 8))
        
        self.issuer_entry = tk.Entry(
            form_frame,
            font=('Segoe UI', 11),
            bg='#f8f9fa',
            fg='#202124',
            relief='flat',
            bd=8,
            highlightthickness=1,
            highlightcolor='#1a73e8',
            highlightbackground='#e0e0e0'
        )
        self.issuer_entry.pack(fill='x', pady=(0, 20), ipady=8)
        
        secret_label_frame = tk.Frame(form_frame, bg='white')
        secret_label_frame.pack(fill='x', pady=(0, 8))
        
        tk.Label(
            secret_label_frame,
            text="Chave secreta",
            font=('Segoe UI', 10, 'bold'),
            fg='#202124',
            bg='white'
        ).pack(side='left')
        
        tk.Label(
            secret_label_frame,
            text="*",
            font=('Segoe UI', 10, 'bold'),
            fg='#ea4335',
            bg='white'
        ).pack(side='left')
        
        self.secret_entry = tk.Entry(
            form_frame,
            font=('JetBrains Mono', 10),
            bg='#f8f9fa',
            fg='#202124',
            relief='flat',
            bd=8,
            highlightthickness=1,
            highlightcolor='#1a73e8',
            highlightbackground='#e0e0e0',
            show='•'
        )
        self.secret_entry.pack(fill='x', pady=(0, 10), ipady=8)
        
        self.show_secret_var = tk.BooleanVar()
        show_check = tk.Checkbutton(
            form_frame,
            text="Mostrar chave secreta",
            font=('Segoe UI', 9),
            fg='#5f6368',
            bg='white',
            activebackground='white',
            activeforeground='#5f6368',
            selectcolor='white',
            variable=self.show_secret_var,
            command=self.toggle_secret_visibility,
            relief='flat',
            bd=0
        )
        show_check.pack(anchor='w', pady=(0, 15))
        
        self.secret_entry.bind('<KeyRelease>', self.validate_secret)
        
        self.status_frame = tk.Frame(form_frame, bg='white')
        self.status_frame.pack(fill='x', pady=(0, 10))
        
        self.status_label = tk.Label(
            self.status_frame,
            text="",
            font=('Segoe UI', 9),
            bg='white'
        )
        self.status_label.pack(anchor='w')
        
        help_frame = tk.Frame(form_frame, bg='#f8f9fa', relief='flat', bd=1)
        help_frame.pack(fill='x', pady=(10, 0))
        
        help_content = tk.Frame(help_frame, bg='#f8f9fa')
        help_content.pack(fill='x', padx=15, pady=15)
        
        tk.Label(
            help_content,
            text="💡 Dica",
            font=('Segoe UI', 9, 'bold'),
            fg='#1a73e8',
            bg='#f8f9fa'
        ).pack(anchor='w')
        
        tk.Label(
            help_content,
            text="A chave secreta geralmente tem 16+ caracteres\ne contém apenas letras A-Z e números 2-7.",
            font=('Segoe UI', 9),
            fg='#5f6368',
            bg='#f8f9fa',
            justify='left'
        ).pack(anchor='w', pady=(5, 0))
    
    def toggle_secret_visibility(self):
        """Mostra/oculta chave secreta"""
        if self.show_secret_var.get():
            self.secret_entry.configure(show='')
        else:
            self.secret_entry.configure(show='•')
    
    def validate_secret(self, event=None):
        """Valida chave secreta em tempo real"""
        secret = self.secret_entry.get().strip()
        if not secret:
            self.status_label.configure(text="", fg='#5f6368')
            return
        
        is_valid, message = self.totp_generator.validate_secret(secret)
        if is_valid:
            self.status_label.configure(text="✓ Chave válida", fg='#137333')
        else:
            self.status_label.configure(text=f"✗ {message}", fg='#ea4335')
    
    def add_account(self):
        """Adiciona a conta"""
        name = self.name_entry.get().strip()
        secret = self.secret_entry.get().strip()
        issuer = self.issuer_entry.get().strip()
        
        if not name:
            messagebox.showerror("Erro", "Nome da conta é obrigatório", parent=self.dialog)
            self.name_entry.focus()
            return

        if not secret:
            messagebox.showerror("Erro", "Chave secreta é obrigatória", parent=self.dialog)
            self.secret_entry.focus()
            return

        is_valid, message = self.totp_generator.validate_secret(secret)
        if not is_valid:
            messagebox.showerror("Erro", f"Chave secreta inválida:\n{message}", parent=self.dialog)
            self.secret_entry.focus()
            return
        
        self.result = {
            'name': name,
            'secret': self.totp_generator.clean_secret(secret),
            'issuer': issuer
        }
        
        self.dialog.destroy()
    
    def cancel(self):
        """Cancela o diálogo"""
        self.result = None
        self.dialog.destroy()
    
    def bring_to_front(self):
        self.dialog.deiconify()
        self.dialog.lift()
        self.dialog.focus_force()

    def show(self):
        """Mostra o diálogo e retorna resultado"""
        self.dialog.wait_window()
        return self.result