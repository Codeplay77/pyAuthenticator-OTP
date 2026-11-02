"""Small, theme-aware Tk components. Icons use the existing Pillow dependency."""

import tkinter as tk
from tkinter import font as tkfont

from PIL import Image, ImageDraw, ImageTk


def icon_art(name, color, size=24):
    """Draw crisp, font-independent icons on a transparent background."""
    scale = 4
    image = Image.new('RGBA', (size * scale, size * scale))
    draw = ImageDraw.Draw(image)
    unit = size * scale / 24

    def points(values):
        return [round(v * unit) for v in values]

    def line(values):
        draw.line(points(values), fill=color, width=max(1, round(1.8 * unit)), joint='curve')

    def box(values, radius=2):
        draw.rounded_rectangle(points(values), radius=radius * unit,
                               outline=color, width=max(1, round(1.8 * unit)))

    def oval(values):
        draw.ellipse(points(values), outline=color, width=max(1, round(1.8 * unit)))

    if name == 'shield':
        line([12, 2, 21, 6, 20, 14, 17, 19, 12, 22, 7, 19, 4, 14, 3, 6, 12, 2])
        line([8, 12, 11, 15, 16, 9])
    elif name == 'plus':
        line([12, 5, 12, 19])
        line([5, 12, 19, 12])
    elif name == 'copy':
        box([8, 8, 20, 21])
        line([5, 16, 3, 16, 3, 3, 15, 3, 15, 5])
    elif name == 'key':
        oval([2, 3, 12, 13])
        line([11, 12, 21, 22, 23, 20, 20, 17, 18, 19])
    elif name == 'trash':
        line([4, 6, 20, 6])
        line([9, 5, 9, 3, 15, 3, 15, 5])
        line([6, 8, 7, 21, 17, 21, 18, 8])
        line([10, 10, 10, 17])
        line([14, 10, 14, 17])
    elif name == 'sun':
        oval([7, 7, 17, 17])
        for ray in ([12, 1, 12, 4], [12, 20, 12, 23], [1, 12, 4, 12],
                    [20, 12, 23, 12], [4, 4, 6, 6], [18, 18, 20, 20],
                    [4, 20, 6, 18], [18, 6, 20, 4]):
            line(ray)
    elif name == 'moon':
        line([19, 16, 16, 17, 12, 16, 9, 13, 8, 9, 9, 5, 11, 2,
              6, 4, 3, 8, 2, 12, 4, 18, 9, 21, 14, 21, 18, 19, 21, 15, 19, 16])
    elif name == 'check':
        line([4, 12, 9, 17, 20, 6])
    elif name == 'lock':
        box([5, 10, 19, 22])
        draw.arc(points([7, 2, 17, 16]), 180, 360, fill=color,
                 width=max(1, round(1.8 * unit)))
        line([12, 14, 12, 18])
    else:
        raise ValueError('Unknown icon: ' + name)
    return image.resize((size, size), getattr(Image, 'Resampling', Image).LANCZOS)


def scaled(widget, value):
    """Scale pixel dimensions alongside Tk's point-sized fonts."""
    return round(value * max(1, float(widget.tk.call('tk', 'scaling')) / (96 / 72)))


def icon_image(widget, name, color, size=20):
    size = scaled(widget, size)
    return ImageTk.PhotoImage(icon_art(name, color, size), master=widget)


def icon_label(parent, name, color, background, size=24, **kwargs):
    label = tk.Label(parent, bg=background, **kwargs)
    label.image = icon_image(label, name, color, size)
    label.configure(image=label.image)
    return label


class Tooltip:
    """Hints available on hover and keyboard focus, cleaned up with the widget."""

    def __init__(self, widget, text, colors):
        self.widget, self.text, self.colors = widget, text, colors
        self.job = self.window = None
        for event in ('<Enter>', '<FocusIn>'):
            widget.bind(event, self.schedule, add='+')
        for event in ('<Leave>', '<FocusOut>', '<ButtonPress>', '<Destroy>'):
            widget.bind(event, self.hide, add='+')

    def schedule(self, event=None):
        self.hide()
        self.job = self.widget.after(600, self.show)

    def show(self):
        self.job = None
        self.window = tk.Toplevel(self.widget)
        self.window.overrideredirect(True)
        self.window.configure(bg=self.colors['border'])
        tk.Label(self.window, text=self.text, bg=self.colors['surface_alt'],
                 fg=self.colors['text'], font=('Segoe UI', 9), padx=10, pady=6,
                 wraplength=280, justify='left').pack(padx=1, pady=1)
        self.window.update_idletasks()
        x = min(self.widget.winfo_rootx(),
                self.window.winfo_screenwidth() - self.window.winfo_reqwidth() - 8)
        y = min(self.widget.winfo_rooty() + self.widget.winfo_height() + 6,
                self.window.winfo_screenheight() - self.window.winfo_reqheight() - 8)
        self.window.geometry(f'+{max(0, x)}+{max(0, y)}')

    def hide(self, event=None):
        if self.job:
            self.widget.after_cancel(self.job)
            self.job = None
        if self.window:
            self.window.destroy()
            self.window = None


def action_button(parent, colors, text='', command=None, icon=None,
                  variant='secondary', hint=None, background=None, compact=False):
    base = background or colors['surface']
    if variant in ('primary', 'danger'):
        bg, fg = colors[variant], colors['on_' + variant]
        hover, hover_fg = colors[variant + '_active'], fg
    elif variant == 'danger_ghost':
        bg, fg = base, colors['text_secondary']
        hover, hover_fg = colors['error_soft'], colors['error']
    else:
        bg = base if variant == 'ghost' else colors['accent_soft']
        fg = colors['text_secondary'] if variant == 'ghost' else colors['accent']
        hover, hover_fg = colors['accent_soft'], colors['accent']
    button = tk.Button(
        parent, text=('  ' + text if icon and text else text), command=command,
        font=('Segoe UI', 10, 'bold'), bg=bg, fg=fg,
        activebackground=hover, activeforeground=hover_fg,
        disabledforeground=colors['text_muted'], relief='flat', bd=0,
        highlightthickness=1, highlightbackground=bg, highlightcolor=colors['accent'],
        padx=8 if compact else 14, pady=7 if compact else 10,
        cursor='hand2', takefocus=True, compound='left')
    if icon:
        button.icon = icon_image(button, icon, fg)
        button.hover_icon = icon_image(button, icon, hover_fg)
        button.configure(image=button.icon)

    def paint(entered):
        if str(button['state']) != 'disabled':
            button.configure(bg=hover if entered else bg, fg=hover_fg if entered else fg)
            if icon:
                button.configure(image=button.hover_icon if entered else button.icon)

    button.bind('<Enter>', lambda e: paint(True), add='+')
    button.bind('<Leave>', lambda e: paint(False), add='+')
    button.bind('<Return>', lambda e: (button.invoke(), 'break')[1])
    if hint:
        button.tooltip = Tooltip(button, hint, colors)
    return button


class ElidedLabel(tk.Label):
    """Keep account names on one line without pushing the actions offscreen."""

    def __init__(self, parent, text, colors, **kwargs):
        super().__init__(parent, text=text, anchor='w', **kwargs)
        self.full_text = text
        self.tooltip = Tooltip(self, text, colors)
        self.bind('<Configure>', self.fit)

    def fit(self, event):
        font = tkfont.Font(font=self['font'])
        available = max(0, event.width - 6)
        text = self.full_text
        if font.measure(text) > available:
            low, high = 0, len(text)
            while low < high:
                mid = (low + high + 1) // 2
                if font.measure(text[:mid] + '…') <= available:
                    low = mid
                else:
                    high = mid - 1
            text = text[:low] + '…'
        self.configure(text=text)
