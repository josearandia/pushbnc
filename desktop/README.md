# Cliente Desktop BNC (Python)

Aplicacion de escritorio para Linux y Windows que:

1. Pide cédula.
2. Consulta API HTTPS para buscar registros no procesados.
3. Muestra registros en una lista para seleccionar.
4. Al presionar Enter sobre una seleccion, marca `procesado=true`.
5. Abre popup centrado con botones para copiar:
   - destiny_bank_reference
   - OriginBankCode
   - ClientID
   - ClientPhone
   - Amount

## Requisitos

- Python 3.10+
- API HTTPS desplegada y accesible

## Configuracion

1. Copiar `datos.env.example` como `datos.env`.
2. Completar:

```ini
API_BASE_URL=https://tu-dominio-api.com
API_BEARER_TOKEN=tu_token
REQUEST_TIMEOUT_SECONDS=10
```

Notas:

- En desarrollo, la app busca primero `desktop/datos.env` y luego `desktop/.env`.
- En ejecutable (`bncpush.exe`), la app busca `datos.env` en la misma carpeta del `.exe`.

## Ejecutar

```bash
cd desktop
python -m venv .venv
source .venv/bin/activate  # Linux
# .venv\Scripts\activate    # Windows PowerShell
pip install -r requirements.txt
python main.py
```
