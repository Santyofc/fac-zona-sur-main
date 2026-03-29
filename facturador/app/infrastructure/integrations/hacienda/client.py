import base64

import httpx

from app.core.config import settings
from app.infrastructure.integrations.hacienda.auth import HaciendaAuthClient
from app.infrastructure.integrations.hacienda.mapper import HaciendaMapper


class HaciendaHTTPClient:
    def __init__(self):
        self.auth = HaciendaAuthClient()

    async def submit(self, payload: dict) -> dict:
        request_payload = {
            'clave': payload['clave'],
            'fecha': payload['issue_date'].strftime('%Y-%m-%dT%H:%M:%S-06:00'),
            'emisor': payload['emisor'],
            'comprobanteXml': base64.b64encode(payload['xml_signed'].encode('utf-8')).decode('utf-8'),
        }
        for attempt in range(2):
            token = await self.auth.get_token(force_refresh=attempt > 0)
            async with httpx.AsyncClient(timeout=35) as client:
                response = await client.post(
                    f"{settings.HACIENDA_API_URL}/recepcion",
                    json=request_payload,
                    headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
                )
            if response.status_code == 401 and attempt == 0:
                continue
            if response.status_code not in (200, 201, 202):
                response.raise_for_status()
            mapped = HaciendaMapper.map_submit_response(response.json() if response.content else {'ind-estado': 'procesando'})
            mapped['clave'] = payload['clave']
            mapped['consecutive'] = payload['consecutive']
            return mapped
        raise RuntimeError('failed to submit to Hacienda after token refresh')

    async def get_status(self, clave: str) -> dict:
        for attempt in range(2):
            token = await self.auth.get_token(force_refresh=attempt > 0)
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.get(
                    f"{settings.HACIENDA_API_URL}/recepcion/{clave}",
                    headers={'Authorization': f'Bearer {token}'},
                )
            if response.status_code == 401 and attempt == 0:
                continue
            if response.status_code == 404:
                return {'hacienda_status': 'no_encontrado', 'message': 'No encontrado'}
            response.raise_for_status()
            return HaciendaMapper.map_status_response(response.json())
        raise RuntimeError('failed to query Hacienda status')
