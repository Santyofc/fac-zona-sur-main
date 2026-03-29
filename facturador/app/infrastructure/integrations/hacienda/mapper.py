class HaciendaMapper:
    @staticmethod
    def map_submit_response(resp: dict) -> dict:
        status = resp.get('ind-estado', 'procesando')
        return {
            'hacienda_status': status,
            'message': resp.get('detalle') or resp.get('message', ''),
            'raw': resp,
        }

    @staticmethod
    def map_status_response(resp: dict) -> dict:
        return {
            'hacienda_status': resp.get('ind-estado', 'procesando').lower(),
            'message': resp.get('detalle', ''),
            'raw': resp,
        }
