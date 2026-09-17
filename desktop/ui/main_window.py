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
        search_frame = ttk.LabelFrame(self, text='Registros pendientes', padding=10)
        search_frame.grid(row=0, column=0, sticky='ew')

        ttk.Label(search_frame, text='Referencia:').grid(row=0, column=0, padx=(0, 8), pady=4, sticky='w')
        self.referencia_var = tk.StringVar()
        only_digits = (self.register(self._is_numeric_input), '%P')
        self.referencia_entry = ttk.Entry(
            search_frame,
            textvariable=self.referencia_var,
            width=4,
            validate='key',
            validatecommand=only_digits,
        )
        self.referencia_entry.grid(row=0, column=1, padx=(0, 8), pady=4, sticky='w')
        self.referencia_entry.focus_set()

        self.search_btn = ttk.Button(search_frame, text='Buscar Pendientes', command=self.search_pending)
        self.search_btn.grid(row=0, column=2, pady=4, sticky='w')
        self.search_btn.config(default='active')

        self.status_var = tk.StringVar(value='Presione Buscar Pendientes para consultar los registros.')
        ttk.Label(self, textvariable=self.status_var).grid(row=1, column=0, pady=(10, 6), sticky='w')

        list_frame = ttk.LabelFrame(self, text='Registros no procesados', padding=10)
        list_frame.grid(row=2, column=0, sticky='nsew')
        self.rowconfigure(2, weight=1)
        self.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)

        columns = ('rowid', 'referencia', 'banco', 'cedula', 'telefono', 'monto', 'fecha_tx', 'hora_tx', 'tipo', 'fecha_registro')
        self.records_table = ttk.Treeview(list_frame, columns=columns, show='headings', selectmode='browse')
        headings = ('ROWID', 'REF. DESTINO', 'BANCO ORIGEN', 'CEDULA/RIF', 'TELEFONO', 'MONTO', 'FECHA TX', 'HORA TX', 'TIPO', 'FECHA REGISTRO')
        widths = (70, 155, 110, 120, 135, 110, 105, 85, 85, 150)
        for column, heading, width in zip(columns, headings, widths):
            self.records_table.heading(column, text=heading)
            self.records_table.column(column, width=width, minwidth=width, anchor='w')

        self.records_table.grid(row=0, column=0, sticky='nsew')
        self.records_table.bind('<Return>', lambda _event: self.process_selected())
        self.records_table.bind('<Double-Button-1>', lambda _event: self.process_selected())
        self.records_table.bind('<FocusIn>', lambda _event: self._set_default_action('process'))

        vertical_scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.records_table.yview)
        vertical_scrollbar.grid(row=0, column=1, sticky='ns')
        horizontal_scrollbar = ttk.Scrollbar(list_frame, orient='horizontal', command=self.records_table.xview)
        horizontal_scrollbar.grid(row=1, column=0, sticky='ew')
        self.records_table.config(yscrollcommand=vertical_scrollbar.set, xscrollcommand=horizontal_scrollbar.set)

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
        self.referencia_entry.config(state=state)

    @staticmethod
    def _is_numeric_input(value: str) -> bool:
        return len(value) <= 20 and (not value or value.isdigit())

    def search_pending(self) -> None:
        referencia = self.referencia_var.get().strip()
        if not 4 <= len(referencia) <= 20:
            messagebox.showwarning('Validacion', 'Ingrese una referencia numerica de 4 a 20 digitos.')
            self.referencia_entry.focus_set()
            return

        self._set_loading(True)
        self.status_var.set('Consultando registros pendientes...')

        thread = threading.Thread(target=self._search_pending_task, args=(referencia,), daemon=True)
        thread.start()

    def _search_pending_task(self, referencia: str) -> None:
        try:
            records = self.api_client.get_pending(referencia)
            self.root.after(0, lambda: self._on_search_success(records))
        except ApiError as exc:
            message = str(exc)
            self.root.after(0, lambda: self._on_error(message))

    def _on_search_success(self, records: list[NotificationRecord]) -> None:
        self.records = records
        for item_id in self.records_table.get_children():
            self.records_table.delete(item_id)

        if not records:
            self.status_var.set('No hay registros pendientes.')
            self._set_loading(False)
            self.referencia_entry.focus_set()
            self._set_default_action('search')
            return

        for rec in records:
            self.records_table.insert(
                '',
                tk.END,
                iid=str(rec.rowid),
                values=(
                    rec.rowid,
                    rec.destiny_bank_reference,
                    rec.origin_bank_code,
                    rec.client_id,
                    rec.client_phone,
                    rec.amount,
                    rec.tx_date,
                    rec.tx_hour,
                    rec.payment_type,
                    rec.fecha_registro,
                ),
            )

        first_record = str(records[0].rowid)
        self.records_table.selection_set(first_record)
        self.records_table.focus(first_record)
        self.records_table.focus_set()
        self._set_default_action('process')
        self.status_var.set(f'Se encontraron {len(records)} registro(s). Seleccione uno y presione Enter.')
        self._set_loading(False)

    def process_selected(self) -> None:
        if not self.records:
            messagebox.showinfo('Informacion', 'No hay registros para procesar.')
            return

        referencia = self.referencia_var.get().strip()
        if not 4 <= len(referencia) <= 20:
            messagebox.showwarning('Validacion', 'Ingrese una referencia numerica de 4 a 20 digitos.')
            self.referencia_entry.focus_set()
            return

        selected = self.records_table.selection()
        if not selected:
            messagebox.showwarning('Validacion', 'Seleccione un registro en la tabla.')
            return

        rowid = int(selected[0])
        index = next(index for index, item in enumerate(self.records) if item.rowid == rowid)
        record = self.records[index]
        self.status_var.set('Revise los datos y presione Cerrar para procesar el registro seleccionado.')
        DetailPopup(
            self.root,
            record,
            on_close=lambda popup_record: self._process_after_popup_close(popup_record, index, int(referencia)),
        )

    def _process_after_popup_close(self, record: NotificationRecord, index: int, referencia: int) -> None:
        self._set_loading(True)
        self.status_var.set(f'Procesando rowid {record.rowid}...')

        thread = threading.Thread(target=self._process_task, args=(record.rowid, index, referencia), daemon=True)
        thread.start()

    def _process_task(self, rowid: int, index: int, referencia: int) -> None:
        try:
            processed_record = self.api_client.mark_processed(rowid, referencia)
            self.root.after(0, lambda: self._on_process_success(processed_record, index))
        except ApiError as exc:
            message = str(exc)
            self.root.after(0, lambda: self._on_error(message))

    def _on_process_success(self, processed_record: NotificationRecord, index: int) -> None:
        self.status_var.set(f'rowid {processed_record.rowid} procesado correctamente.')

        self.records = []
        for item_id in self.records_table.get_children():
            self.records_table.delete(item_id)
        self.referencia_var.set('')
        self.status_var.set('Listo para procesar otro registro.')
        self.referencia_entry.focus_set()
        self._set_default_action('search')

        self._set_loading(False)

    def _on_error(self, message: str) -> None:
        self._set_loading(False)
        self.status_var.set('Ocurrio un error, revise el detalle.')
        self.referencia_entry.focus_set()
        self._set_default_action('search')
        messagebox.showerror('Error', message)
