# API BNC Push Notificaciones

## Variables de entorno

Copia `.env.example` a `.env` y configura:

- `DB_HOST`
- `DB_PORT`
- `DB_NAME`
- `DB_USER`
- `DB_PASS`
- `API_BEARER_TOKEN`

## Ejecutar local

```bash
cd api
php -S 0.0.0.0:8080
```

## Endpoints

### 1) Listar pendientes por cedula

- Metodo: `GET`
- URL: `/notificaciones.php?cedula=V12345678`
- Header: `Authorization: Bearer <token>`

Respuesta:

```json
{
  "ok": true,
  "count": 1,
  "data": [
    {
      "rowid": 10,
      "destiny_bank_reference": "REF001",
      "origin_bank_code": "0102",
      "client_id": "V12345678",
      "client_phone": "04120000000",
      "amount": "100.00"
    }
  ]
}
```

### 2) Marcar procesado por rowid

- Metodo: `POST`
- URL: `/procesar.php`
- Header: `Authorization: Bearer <token>`
- Body JSON:

```json
{
  "rowid": 10
}
```

Respuesta (exito):

```json
{
  "ok": true,
  "updated": true,
  "message": "Registro procesado correctamente",
  "data": {
    "rowid": 10,
    "destiny_bank_reference": "REF001",
    "origin_bank_code": "0102",
    "client_id": "V12345678",
    "client_phone": "04120000000",
    "amount": "100.00"
  }
}
```
