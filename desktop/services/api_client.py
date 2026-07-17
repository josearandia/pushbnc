from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

import requests


@dataclass
class NotificationRecord:
    rowid: int
    destiny_bank_reference: str
    origin_bank_code: str
    client_id: str
    client_phone: str
    amount: str

    @property
    def amount_decimal(self) -> Decimal:
        try:
            return Decimal(str(self.amount))
        except Exception:
            return Decimal('0.00')


class ApiError(Exception):
    pass


class ApiClient:
    def __init__(self, base_url: str, bearer_token: str, timeout_seconds: int = 10) -> None:
        self.base_url = base_url.rstrip('/')
        self.timeout_seconds = timeout_seconds
        self.session = requests.Session()
        self.session.headers.update(
            {
                'Authorization': f'Bearer {bearer_token}',
                'Accept': 'application/json',
                'Content-Type': 'application/json',
            }
        )

    def get_pending_by_cedula(self, cedula: str) -> list[NotificationRecord]:
        url = f'{self.base_url}/notificaciones.php'
        try:
            response = self.session.get(
                url,
                params={'cedula': cedula},
                timeout=self.timeout_seconds,
            )
        except requests.RequestException as exc:
            raise ApiError(f'Error de red consultando API: {exc}') from exc

        payload = self._parse_response(response)
        data = payload.get('data', [])
        if not isinstance(data, list):
            raise ApiError('Respuesta inesperada del servidor en data')

        records: list[NotificationRecord] = []
        for item in data:
            if not isinstance(item, dict):
                continue
            records.append(self._to_record(item))

        return records

    def mark_processed(self, rowid: int) -> NotificationRecord:
        url = f'{self.base_url}/procesar.php'
        try:
            response = self.session.post(
                url,
                json={'rowid': rowid},
                timeout=self.timeout_seconds,
            )
        except requests.RequestException as exc:
            raise ApiError(f'Error de red actualizando registro: {exc}') from exc

        payload = self._parse_response(response)
        data = payload.get('data')
        if not isinstance(data, dict):
            raise ApiError('Respuesta inesperada del servidor en data')

        return self._to_record(data)

    @staticmethod
    def _to_record(item: dict[str, Any]) -> NotificationRecord:
        return NotificationRecord(
            rowid=int(item.get('rowid', 0)),
            destiny_bank_reference=str(item.get('destiny_bank_reference', '') or ''),
            origin_bank_code=str(item.get('origin_bank_code', '') or ''),
            client_id=str(item.get('client_id', '') or ''),
            client_phone=str(item.get('client_phone', '') or ''),
            amount=str(item.get('amount', '') or ''),
        )

    @staticmethod
    def _parse_response(response: requests.Response) -> dict[str, Any]:
        try:
            payload = response.json()
        except ValueError as exc:
            raise ApiError(f'La API no retorno JSON valido (HTTP {response.status_code})') from exc

        if not response.ok:
            message = payload.get('error') if isinstance(payload, dict) else None
            raise ApiError(message or f'Error HTTP {response.status_code}')

        if not isinstance(payload, dict):
            raise ApiError('Respuesta JSON invalida, se esperaba objeto')

        if not payload.get('ok', False):
            raise ApiError(str(payload.get('error', 'Error no especificado')))

        return payload
