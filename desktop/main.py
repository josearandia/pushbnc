from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from config import load_settings
from services.api_client import ApiClient
from ui.main_window import MainWindow


def main() -> None:
    root = tk.Tk()

    style = ttk.Style(root)
    if 'clam' in style.theme_names():
        style.theme_use('clam')

    try:
        settings = load_settings()
    except Exception as exc:
        root.withdraw()
        messagebox.showerror('Configuracion invalida', str(exc))
        root.destroy()
        return

    api_client = ApiClient(
        base_url=settings.api_base_url,
        bearer_token=settings.api_bearer_token,
        timeout_seconds=settings.timeout_seconds,
    )

    MainWindow(root, api_client)
    root.mainloop()


if __name__ == '__main__':
    main()
