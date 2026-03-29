from datetime import datetime, timedelta

import httpx

from app.core.config import settings


class HaciendaAuthClient:
    def __init__(self):
        self._token = None
        self._expires_at = datetime.min

    async def get_token(self, force_refresh: bool = False) -> str:
        now = datetime.utcnow()
        if not force_refresh and self._token and self._expires_at > now:
            return self._token

        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                settings.HACIENDA_TOKEN_URL,
                data={
                    'grant_type': 'password',
                    'client_id': settings.HACIENDA_CLIENT_ID,
                    'client_secret': settings.HACIENDA_CLIENT_SECRET,
                    'username': settings.HACIENDA_USERNAME,
                    'password': settings.HACIENDA_PASSWORD,
                },
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
            )
            response.raise_for_status()
            data = response.json()
            self._token = data['access_token']
            ttl = int(data.get('expires_in', 300)) - 20
            self._expires_at = now.replace(microsecond=0) + timedelta(seconds=ttl)
            return self._token
