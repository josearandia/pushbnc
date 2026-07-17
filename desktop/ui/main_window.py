from __future__ import annotations

import threading
import tkinter as tk
from tkinter import messagebox, ttk

from services.api_client import ApiClient, ApiError, NotificationRecord
from ui.detail_popup import DetailPopup


class MainWindow(ttk.Frame):
    def __init__(self, root: tk.Tk, api_client: ApiClient) -> None:
        super().__init__(root, padding=14)
        self.root = root
        self.api_client = api_client
        self.records: list[NotificationRecord] = []

        self.root.title('BNC Push Notificaciones')
        self.root.geometry('860x460')
        self.root.minsize(760, 420)

        self.grid(row=0, column=0, sticky='nsew')
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        self._build_ui()
        self.root.after(0, self.position_bottom_right)

    def position_bottom_right(self) -> None:
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        margin = 20
        x = max(0, int(screen_width - width - margin))
        y = max(0, int(screen_height - height - margin))
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def _build_ui(self) -> None:
        search_frame = ttk.LabelFrame(self, text='Busqueda por cedula', padding=10)
        search_frame.grid(row=0, column=0, sticky='ew')

        ttk.Label(search_frame, text='Tipo ID:').grid(row=0, column=0, padx=(0, 8), pady=4, sticky='w')

        self.id_prefix_var = tk.StringVar(value='V')
        self.id_prefix_combo = ttk.Combobox(
            search_frame,
            textvariable=self.id_prefix_var,
            values=['V', 'J', 'G', 'E'],
            state='readonly',
            width=4,
        )
        self.id_prefix_combo.grid(row=0, column=1, padx=(0, 8), pady=4, sticky='w')

        ttk.Label(search_frame, text='Cedula:').grid(row=0, column=2, padx=(0, 8), pady=4, sticky='w')

        self.cedula_var = tk.StringVar()
        self.cedula_entry = ttk.Entry(search_frame, textvariable=self.cedula_var, width=28)
        self.cedula_entry.grid(row=0, column=3, padx=(0, 8), pady=4, sticky='w')
        self.cedula_entry.focus_set()
        self.cedula_entry.bind('<Return>', lambda _event: self.search_pending())
        self.cedula_entry.bind('<FocusIn>', lambda _event: self._set_default_action('search'))

        self.search_btn = ttk.Button(search_frame, text='Buscar Pendientes', command=self.search_pending)
        self.search_btn.grid(row=0, column=4, pady=4, sticky='w')
        self.search_btn.config(default='active')

        self.status_var = tk.StringVar(value='Escriba una cedula y presione Enter o Buscar Pendientes.')
        ttk.Label(self, textvariable=self.status_var).grid(row=1, column=0, pady=(10, 6), sticky='w')

        list_frame = ttk.LabelFrame(self, text='Registros no procesados', padding=10)
        list_frame.grid(row=2, column=0, sticky='nsew')
        self.rowconfigure(2, weight=1)
        self.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)

        self.listbox = tk.Listbox(list_frame, height=12)
        self.listbox.grid(row=0, column=0, sticky='nsew')
        self.listbox.bind('<Return>', lambda _event: self.process_selected())
        self.listbox.bind('<Double-Button-1>', lambda _event: self.process_selected())
        self.listbox.bind('<FocusIn>', lambda _event: self._set_default_action('process'))

        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.listbox.yview)
        scrollbar.grid(row=0, column=1, sticky='ns')
        self.listbox.config(yscrollcommand=scrollbar.set)

        actions = ttk.Frame(self)
        actions.grid(row=3, column=0, pady=(8, 0), sticky='e')

        self.process_btn = ttk.Button(actions, text='Procesar Seleccionado (Enter)', command=self.process_selected)
        self.process_btn.grid(row=0, column=0)

    def _set_default_action(self, action: str) -> None:
        if action == 'search':
            self.search_btn.config(default='active')
            self.process_btn.config(default='normal')
            return

        if action == 'process':
            self.search_btn.config(default='normal')
            self.process_btn.config(default='active')
            return

        self.search_btn.config(default='normal')
        self.process_btn.config(default='normal')

    def _set_loading(self, loading: bool) -> None:
        state = 'disabled' if loading else 'normal'
        self.search_btn.config(state=state)
        self.process_btn.config(state=state)
        self.cedula_entry.config(state=state)

    def search_pending(self) -> None:
        cedula = self.cedula_var.get().strip()
        if not cedula:
            messagebox.showwarning('Validacion', 'Ingrese una cedula para buscar.')
            return

        prefix = self.id_prefix_var.get().strip().upper() or 'V'
        cedula_compuesta = f'{prefix}{cedula}'

        self._set_loading(True)
        self.status_var.set('Consultando registros pendientes...')

        thread = threading.Thread(target=self._search_pending_task, args=(cedula_compuesta,), daemon=True)
        thread.start()

    def _search_pending_task(self, cedula: str) -> None:
        try:
            records = self.api_client.get_pending_by_cedula(cedula)
            self.root.after(0, lambda: self._on_search_success(records))
        except ApiError as exc:
            self.root.after(0, lambda: self._on_error(str(exc)))

    def _on_search_success(self, records: list[NotificationRecord]) -> None:
        self.records = records
        self.listbox.delete(0, tk.END)

        if not records:
            self.status_var.set('No hay registros pendientes para esa cedula.')
            self._set_loading(False)
            self.cedula_entry.focus_set()
            self._set_default_action('search')
            return

        for rec in records:
            item = (
                f'rowid={rec.rowid} | ref={rec.destiny_bank_reference} '
                f'| banco={rec.origin_bank_code} | tel={rec.client_phone} | monto={rec.amount}'
            )
            self.listbox.insert(tk.END, item)

        self.listbox.selection_set(0)
        self.listbox.activate(0)
        self.listbox.focus_set()
        self._set_default_action('process')
        self.status_var.set(f'Se encontraron {len(records)} registro(s). Seleccione uno y presione Enter.')
        self._set_loading(False)

    def process_selected(self) -> None:
        if not self.records:
            messagebox.showinfo('Informacion', 'No hay registros para procesar.')
            return

        selected = self.listbox.curselection()
        if not selected:
            messagebox.showwarning('Validacion', 'Seleccione un registro en la lista.')
            return

        index = selected[0]
        record = self.records[index]
        self.status_var.set('Revise los datos y presione Cerrar para procesar el registro seleccionado.')
        DetailPopup(self.root, record, on_close=lambda popup_record: self._process_after_popup_close(popup_record, index))

    def _process_after_popup_close(self, record: NotificationRecord, index: int) -> None:
        self._set_loading(True)
        self.status_var.set(f'Procesando rowid {record.rowid}...')

        thread = threading.Thread(target=self._process_task, args=(record.rowid, index), daemon=True)
        thread.start()

    def _process_task(self, rowid: int, index: int) -> None:
        try:
            processed_record = self.api_client.mark_processed(rowid)
            self.root.after(0, lambda: self._on_process_success(processed_record, index))
        except ApiError as exc:
            self.root.after(0, lambda: self._on_error(str(exc)))

    def _on_process_success(self, processed_record: NotificationRecord, index: int) -> None:
        self.status_var.set(f'rowid {processed_record.rowid} procesado correctamente.')

        self.records = []
        self.listbox.delete(0, tk.END)
        self.cedula_var.set('')
        self.id_prefix_var.set('V')
        self.status_var.set('Listo para recibir otra cedula.')
        self.cedula_entry.focus_set()
        self._set_default_action('search')

        self._set_loading(False)

    def _on_error(self, message: str) -> None:
        self._set_loading(False)
        self.status_var.set('Ocurrio un error, revise el detalle.')
        self.cedula_entry.focus_set()
        self._set_default_action('search')
        messagebox.showerror('Error', message)
