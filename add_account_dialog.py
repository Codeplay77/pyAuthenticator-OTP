"""
Add Account Dialog Module for Python Authenticator

Provides a modal dialog for adding new 2FA accounts with:
- Account name input (required)
- Service issuer input (optional)
- Secret key input with validation (required)
- Real-time validation feedback
- Show/hide secret key toggle

Colors follow the light or dark palette from theme.py.

Author: Codeplay
Date: June 2025
"""

import tkinter as tk
from tkinter import messagebox, ttk

from theme import PALETTES, apply_title_bar
from ui_components import action_button, icon_label, scaled


class AddAccountDialog:
    def __init__(self, parent, totp_generator, theme_name):
        self.parent = parent
        self.totp_generator = totp_generator
        self.theme_name = theme_name
        self.colors = PALETTES[theme_name]
        self.result = None
        self.setup_dialog()

    def setup_dialog(self):
        colors = self.colors
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title('Adicionar conta')
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        self.dialog.configure(bg=colors['surface'])
        self.dialog.protocol('WM_DELETE_WINDOW', self.cancel)
        self.dialog.bind('<Escape>', lambda e: self.cancel())
        self.dialog.bind('<Return>', lambda e: self.add_account())

        header = tk.Frame(self.dialog, bg=colors['surface'], padx=24, pady=22)
        header.pack(fill='x')
        icon_label(header, 'plus', colors['accent'], colors['accent_soft'],
                   size=24, padx=10, pady=10).pack(side='left', padx=(0, 12))
        heading = tk.Frame(header, bg=colors['surface'])
        heading.pack(side='left', fill='x', expand=True)
        tk.Label(heading, text='Adicionar conta', font=('Segoe UI', 17, 'bold'),
                 fg=colors['text'], bg=colors['surface']).pack(anchor='w')
        tk.Label(heading, text='Seus códigos de verificação, em um só lugar.',
                 font=('Segoe UI', 9), fg=colors['text_secondary'],
                 bg=colors['surface'], wraplength=310, justify='left').pack(anchor='w', pady=(4, 0))
        tk.Frame(self.dialog, bg=colors['border'], height=1).pack(fill='x')

        footer = tk.Frame(self.dialog, bg=colors['surface'], padx=24, pady=18)
        footer.pack(side='bottom', fill='x')
        self.add_btn = action_button(footer, colors, text='Adicionar conta',
                                      icon='plus', variant='primary', command=self.add_account)
        self.add_btn.pack(side='right')
        action_button(footer, colors, text='Cancelar', variant='ghost',
                      command=self.cancel).pack(side='left')

        # Scroll only the form, keeping Save/Cancel available on short displays.
        body = tk.Frame(self.dialog, bg=colors['surface'])
        body.pack(fill='both', expand=True, padx=(24, 14), pady=(18, 0))
        self.form_canvas = tk.Canvas(body, bg=colors['surface'], bd=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(body, orient='vertical', command=self.form_canvas.yview,
                                  style='App.Vertical.TScrollbar')
        scrollbar.pack(side='right', fill='y')
        self.form_canvas.pack(side='left', fill='both', expand=True, padx=(0, 8))
        self.form_canvas.configure(yscrollcommand=scrollbar.set)
        form = tk.Frame(self.form_canvas, bg=colors['surface'])
        form_window = self.form_canvas.create_window(0, 0, window=form, anchor='nw')
        self.form_canvas.bind('<Configure>', lambda e: self.form_canvas.itemconfigure(form_window, width=e.width))
        form.bind('<Configure>', lambda e: self.form_canvas.configure(scrollregion=self.form_canvas.bbox('all')))

        def scroll(event):
            if form.winfo_height() > self.form_canvas.winfo_height():
                steps = int(-event.delta / 120) or (-1 if event.delta > 0 else 1)
                self.form_canvas.yview_scroll(steps, 'units')

        self.dialog.bind('<MouseWheel>', scroll)
        self.setup_manual_form(form)
        self.dialog.update_idletasks()
        width = min(max(scaled(self.dialog, 460), footer.winfo_reqwidth()), self.dialog.winfo_screenwidth() - 40)
        height = min(header.winfo_reqheight() + footer.winfo_reqheight() + form.winfo_reqheight() + 42,
                     self.dialog.winfo_screenheight() - 100)
        self.dialog.minsize(min(width, scaled(self.dialog, 420)), min(height, scaled(self.dialog, 400)))
        x = max(0, min(self.parent.winfo_rootx() + (self.parent.winfo_width() - width) // 2,
                       self.dialog.winfo_screenwidth() - width - 20))
        y = max(0, (self.dialog.winfo_screenheight() - height) // 2)
        self.dialog.geometry(f'{width}x{height}+{x}+{y}')
        apply_title_bar(self.dialog, self.theme_name)
        self.name_entry.focus_force()

    def setup_manual_form(self, parent):
        colors = self.colors

        def field(label, mono=False, secret=False):
            tk.Label(parent, text=label, font=('Segoe UI', 10, 'bold'),
                     fg=colors['text'], bg=colors['surface']).pack(anchor='w', pady=(0, 7))
            entry = tk.Entry(
                parent, font=('Consolas' if mono else 'Segoe UI', 11),
                bg=colors['surface_alt'], fg=colors['text'], insertbackground=colors['text'],
                selectbackground=colors['primary'], selectforeground=colors['on_primary'],
                relief='flat', bd=8, highlightthickness=1,
                highlightcolor=colors['accent'], highlightbackground=colors['border'],
                show='•' if secret else '')
            entry.pack(fill='x', ipady=4, pady=(0, 16))
            entry.bind('<FocusIn>', lambda e: self.reveal_field(entry))
            return entry

        self.name_entry = field('Nome da conta *')
        self.issuer_entry = field('Serviço / emissor (opcional)')
        self.secret_entry = field('Chave secreta *', mono=True, secret=True)
        self.secret_var = tk.StringVar(master=self.dialog)
        self.secret_entry.configure(textvariable=self.secret_var)

        self.show_secret_var = tk.BooleanVar(master=self.dialog)
        tk.Checkbutton(
            parent, text='Mostrar chave secreta', font=('Segoe UI', 9),
            fg=colors['text_secondary'], bg=colors['surface'],
            activebackground=colors['surface'], activeforeground=colors['text'],
            selectcolor=colors['surface_alt'], highlightcolor=colors['accent'],
            highlightbackground=colors['surface'], variable=self.show_secret_var,
            command=self.toggle_secret_visibility, relief='flat', bd=0,
            cursor='hand2').pack(anchor='w', pady=(0, 8))
        self.status_frame = tk.Frame(parent, bg=colors['surface'])
        self.status_frame.pack(fill='x', pady=(0, 12))
        self.status_label = tk.Label(
            self.status_frame, text='', font=('Segoe UI', 9), anchor='w', justify='left',
            fg=colors['text_secondary'], bg=colors['surface'], wraplength=340)
        self.status_label.pack(fill='x')
        self.status_frame.bind('<Configure>', lambda e: self.status_label.configure(wraplength=max(1, e.width - 4)))
        self.secret_var.trace_add('write', lambda *args: self.validate_secret())

        help_frame = tk.Frame(parent, bg=colors['accent_soft'], padx=14, pady=12)
        help_frame.pack(fill='x', pady=(0, 8))
        tk.Label(help_frame, text='Onde encontro a chave?', font=('Segoe UI', 9, 'bold'),
                 fg=colors['accent'], bg=colors['accent_soft']).pack(anchor='w')
        help_label = tk.Label(
            help_frame, text='Nas configurações de segurança do serviço, procure a chave de configuração da autenticação em duas etapas. Use letras A–Z e números 2–7.',
            font=('Segoe UI', 9), fg=colors['text_secondary'], bg=colors['accent_soft'],
            justify='left', wraplength=340)
        help_label.pack(fill='x', pady=(5, 0))
        help_frame.bind('<Configure>', lambda e: help_label.configure(wraplength=max(1, e.width - 32)))

    def reveal_field(self, entry):
        """Keep keyboard navigation usable when the form needs scrolling."""
        self.dialog.update_idletasks()
        canvas = self.form_canvas
        region = canvas.bbox('all')
        if not region or region[3] <= canvas.winfo_height():
            return
        top = entry.winfo_y() - 30
        bottom = entry.winfo_y() + entry.winfo_height() + 8
        visible_top = canvas.canvasy(0)
        if top < visible_top:
            canvas.yview_moveto(max(0, top) / region[3])
        elif bottom > visible_top + canvas.winfo_height():
            canvas.yview_moveto((bottom - canvas.winfo_height()) / region[3])

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
            self.status_label.configure(text="", fg=self.colors['text_secondary'])
            return
        
        is_valid, message = self.totp_generator.validate_secret(secret)
        if is_valid:
            self.status_label.configure(text="Chave válida — pronta para adicionar", fg=self.colors['success'])
        else:
            self.status_label.configure(text=message, fg=self.colors['warning'])
    
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
