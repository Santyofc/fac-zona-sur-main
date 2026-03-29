import uuid


class LocalEmailSender:
    async def send(self, payload: dict) -> dict:
        return {
            'delivery_id': str(uuid.uuid4()),
            'status': 'sent',
            'recipient': payload['to'],
            'provider': 'local',
        }
