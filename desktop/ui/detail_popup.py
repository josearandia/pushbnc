from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable

from services.api_client import NotificationRecord


class DetailPopup(tk.Toplevel):
    def __init__(
        self,
        parent: tk.Misc,
        record: NotificationRecord,
        on_close: Callable[[NotificationRecord], None] | None = None,
    ) -> None:
        super().__init__(parent)
        self.record = record
        self.on_close = on_close

        self.title('Datos de la Transaccion')
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.lift()
        self.protocol('WM_DELETE_WINDOW', self.close_and_notify)

        container = ttk.Frame(self, padding=12)
        container.grid(row=0, column=0, sticky='nsew')

        fields = [
            ('destiny_bank_reference', record.destiny_bank_reference),
            ('OriginBankCode', record.origin_bank_code),
            ('ClientID', record.client_id),
            ('ClientPhone', record.client_phone),
            ('Amount', record.amount),
        ]

        for idx, (label, value) in enumerate(fields):
            ttk.Label(container, text=label + ':', width=22).grid(row=idx, column=0, padx=(0, 8), pady=4, sticky='w')

            display_value = value if value not in (None, '') else '(vacio)'
            value_label = ttk.Label(
                container,
                text=display_value,
                width=36,
                relief='solid',
                padding=(6, 4),
                anchor='w',
            )
            value_label.grid(row=idx, column=1, padx=(0, 8), pady=4, sticky='w')

            button = ttk.Button(
                container,
                text='Copiar',
                command=lambda v=value, b_idx=idx: self.copy_to_clipboard(v, b_idx),
            )
            button.grid(row=idx, column=2, pady=4, sticky='w')

        self.copy_status = ttk.Label(container, text='')
        self.copy_status.grid(row=len(fields), column=0, columnspan=3, pady=(8, 0), sticky='w')

        close_btn = ttk.Button(container, text='Cerrar', command=self.close_and_notify)
        close_btn.grid(row=len(fields) + 1, column=2, pady=(10, 0), sticky='e')

        self.update_idletasks()
        self.position_over_parent_bottom_right()

    def position_over_parent_bottom_right(self) -> None:
        width = self.winfo_width()
        height = self.winfo_height()
        margin = 12

        if self.master is not None and self.master.winfo_ismapped():
            parent_x = self.master.winfo_rootx()
            parent_y = self.master.winfo_rooty()
            parent_width = self.master.winfo_width()
            parent_height = self.master.winfo_height()

            x = int(parent_x + parent_width - width - margin)
            y = int(parent_y + parent_height - height - margin)
        else:
            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()
            x = int(screen_width - width - 20)
            y = int(screen_height - height - 20)

        x = max(0, x)
        y = max(0, y)
        self.geometry(f'{width}x{height}+{x}+{y}')

    def copy_to_clipboard(self, text: str, row_index: int) -> None:
        safe_text = '' if text is None else str(text)
        self.clipboard_clear()
        self.clipboard_append(safe_text)
        self.copy_status.config(text=f'Campo {row_index + 1} copiado al portapapeles')
        self.after(1200, lambda: self.copy_status.config(text=''))

    def close_and_notify(self) -> None:
        if self.on_close is not None:
            self.on_close(self.record)
        self.destroy()
