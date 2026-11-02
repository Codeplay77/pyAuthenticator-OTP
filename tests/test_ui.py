"""UI regressions using synthetic accounts; never open the user's database/config.

Run with: python -m unittest discover -s tests -v
Requires a desktop session for Tk.
"""

import time
import tkinter as tk
import unittest
from unittest.mock import patch

from authenticator_app import AuthenticatorApp
from add_account_dialog import AddAccountDialog
from theme import PALETTES
from token_widget import TokenWidget


SECRET = 'JBSWY3DPEHPK3PXP'


class MemoryConfig:
    def __init__(self):
        self.values = {'ui.theme': 'light', 'tray.enabled': False}

    def get(self, key, default=None):
        return self.values.get(key, default)

    def set(self, key, value):
        self.values[key] = value


class MemoryDatabase:
    def __init__(self):
        self.accounts = [(1, 'demo@example.test', SECRET, 'Example')]

    def get_all_accounts(self):
        return list(self.accounts)

    def delete_account(self, account_id):
        self.accounts = [a for a in self.accounts if a[0] != account_id]


class ThemeUITests(unittest.TestCase):
    def setUp(self):
        self.patches = [patch('authenticator_app.Database', MemoryDatabase),
                        patch('authenticator_app.ConfigManager', MemoryConfig),
                        patch.object(AuthenticatorApp, 'setup_hotkeys'),
                        patch.object(AuthenticatorApp, 'setup_tray')]
        for item in self.patches:
            item.start()
            self.addCleanup(item.stop)
        self.app = AuthenticatorApp()
        self.addCleanup(self.close_app)
        self.errors = []
        self.app.root.report_callback_exception = lambda *args: self.errors.append(args)
        self.app.root.geometry('440x740+80+80')
        self.app.root.update()

    def close_app(self):
        # Multiple Tk interpreters share the event queue in this test process.
        self.app.main_frame.destroy()
        for job in self.app.root.tk.call('after', 'info'):
            self.app.root.after_cancel(job)
        self.app.root.destroy()

    def pump(self, seconds=0.05):
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            self.app.root.update()
            time.sleep(0.005)
        self.assertEqual(self.errors, [])

    def assert_inside(self, widget, container):
        self.assertGreater(widget.winfo_width(), 1)
        self.assertGreater(widget.winfo_height(), 1)
        self.assertGreaterEqual(widget.winfo_rootx(), container.winfo_rootx())
        self.assertGreaterEqual(widget.winfo_rooty(), container.winfo_rooty())
        self.assertLessEqual(widget.winfo_rootx() + widget.winfo_width(),
                             container.winfo_rootx() + container.winfo_width())
        self.assertLessEqual(widget.winfo_rooty() + widget.winfo_height(),
                             container.winfo_rooty() + container.winfo_height())

    def test_both_themes_long_names_and_minimum_window(self):
        self.app.database.accounts = [(1, 'very-long-account-' * 10, SECRET, 'Long service ' * 12)]
        self.app.load_accounts()
        self.app.root.geometry('380x500')
        for expected in ('light', 'dark', 'light'):
            if self.app.theme_name != expected:
                self.app.toggle_theme()
            self.pump()
            card = self.app.token_widgets[0]
            self.assertEqual(card.card['bg'], PALETTES[expected]['surface'])
            for widget in (card.copy_btn, card.recover_btn, card.delete_btn, card.token_label):
                self.assert_inside(widget, card.card)
            self.assertGreaterEqual(card.token_label.winfo_width(), card.token_label.winfo_reqwidth())
            self.assert_inside(self.app.theme_btn, self.app.root)
            self.assert_inside(self.app.status_bar, self.app.root)

    def test_copy_feedback_survives_refresh_and_is_cancelled_on_rebuild(self):
        card = self.app.token_widgets[0]
        card.copy_token()
        self.assertRegex(self.app.root.clipboard_get(), r'^\d{6}$')
        card.update_token()
        self.assertEqual(card.status_label['text'], 'Código copiado')
        pending = card.feedback_job
        self.app.toggle_theme()
        self.assertNotIn(pending, self.app.root.tk.call('after', 'info'))
        self.pump()

    def test_high_dpi_keeps_code_and_actions_visible(self):
        original = self.app.root.tk.call('tk', 'scaling')
        try:
            self.app.root.tk.call('tk', 'scaling', 2.0)
            self.app.main_frame.destroy()
            self.app.token_widgets.clear()
            self.app.setup_ui()
            self.app.load_accounts()
            width, height = self.app.root.minsize()
            self.app.root.geometry(f'{width}x{height}')
            self.pump()
            card = self.app.token_widgets[0]
            self.assertGreaterEqual(card.token_label.winfo_width(), card.token_label.winfo_reqwidth())
            self.assert_inside(card.copy_btn, card.card)
            self.assert_inside(self.app.theme_btn, self.app.root)
            dialog = AddAccountDialog(self.app.root, self.app.totp_generator, self.app.theme_name)
            self.pump()
            self.assert_inside(dialog.add_btn, dialog.dialog)
            self.assert_inside(dialog.secret_entry, dialog.form_canvas)
            dialog.cancel()
        finally:
            self.app.root.tk.call('tk', 'scaling', original)

    def test_secret_copy_requires_confirmation(self):
        card = self.app.token_widgets[0]
        with patch('token_widget.messagebox.askyesno', return_value=False), patch.object(card, 'clipboard_append') as copy:
            card.copy_original_secret()
            copy.assert_not_called()
        with patch('token_widget.messagebox.askyesno', return_value=True), patch('token_widget.messagebox.showinfo'), patch.object(card, 'clipboard_append') as copy:
            card.copy_original_secret()
            copy.assert_called_once_with(SECRET)

    def test_countdown_warning_and_invalid_token(self):
        card = self.app.token_widgets[0]
        with patch.object(card.totp_generator, 'get_time_remaining', return_value=4):
            card.update_token()
            self.assertEqual(card.time_label['fg'], card.colors['warning'])
            self.assertAlmostEqual(float(card.progress_bar.place_info()['relwidth']), 4 / 30, places=3)
        with patch.object(card.totp_generator, 'generate_token', return_value='ERROR'):
            card.update_token()
            self.assertEqual(card.status_label['text'], 'Erro no código')

    def test_count_empty_state_and_scroll_preserved_on_theme_change(self):
        self.app.database.accounts = [(i, f'user{i}@example.test', SECRET, 'Example') for i in range(12)]
        self.app.load_accounts()
        self.pump()
        self.app.canvas.yview_moveto(0.5)
        before = self.app.canvas.yview()[0]
        self.app.toggle_theme()
        self.pump()
        self.assertAlmostEqual(before, self.app.canvas.yview()[0], places=2)
        self.assertEqual(self.app.account_count['text'], '12')
        self.app.database.accounts = []
        self.app.load_accounts()
        self.pump()
        self.assertEqual(self.app.account_count['text'], '0')
        self.assertNotIsInstance(self.app.token_widgets[0], TokenWidget)

    def test_dialog_validation_masking_resize_and_save_in_both_themes(self):
        for theme in ('light', 'dark'):
            if self.app.theme_name != theme:
                self.app.toggle_theme()
            dialog = AddAccountDialog(self.app.root, self.app.totp_generator, theme)
            self.addCleanup(lambda d=dialog: d.dialog.destroy() if d.dialog.winfo_exists() else None)
            self.pump()
            dialog.name_entry.insert(0, 'Test account')
            dialog.secret_entry.insert(0, 'invalid!')
            self.assertEqual(dialog.status_label['fg'], PALETTES[theme]['warning'])
            dialog.secret_entry.delete(0, 'end')
            dialog.secret_entry.insert(0, SECRET.lower())
            self.assertEqual(dialog.status_label['fg'], PALETTES[theme]['success'])
            self.assertEqual(dialog.secret_entry['show'], '•')
            dialog.show_secret_var.set(True)
            dialog.toggle_secret_visibility()
            self.assertEqual(dialog.secret_entry['show'], '')
            dialog.dialog.geometry('420x400')
            self.pump()
            self.assert_inside(dialog.add_btn, dialog.dialog)
            dialog.secret_entry.focus_force()
            self.pump()
            self.assert_inside(dialog.secret_entry, dialog.form_canvas)
            dialog.add_account()
            self.assertEqual(dialog.result, {'name': 'Test account', 'secret': SECRET, 'issuer': ''})

    def test_delete_cancel_is_default_and_confirmation_still_works(self):
        card = self.app.token_widgets[0]
        card.confirm_delete()
        self.pump()
        dialog = self.app.root.grab_current()
        focused = dialog.focus_get()
        self.assertEqual(focused['text'], 'Cancelar')
        focused.event_generate('<Return>')
        self.pump()
        self.assertEqual(len(self.app.database.accounts), 1)
        card.confirm_delete()
        self.pump()
        dialog = self.app.root.grab_current()

        def descendants(widget):
            for child in widget.winfo_children():
                yield child
                yield from descendants(child)

        delete = next(w for w in descendants(dialog) if isinstance(w, tk.Button) and w['text'] == 'Excluir')
        self.assert_inside(delete, dialog)
        delete.invoke()
        self.pump()
        self.assertEqual(self.app.database.accounts, [])


if __name__ == '__main__':
    unittest.main()
