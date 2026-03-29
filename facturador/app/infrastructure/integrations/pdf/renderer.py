class SimplePDFRenderer:
    async def render(self, payload: dict) -> bytes:
        body = f"Factura {payload.get('doc_type')}\nTotal: {payload.get('total', 0)}"
        content = body.encode('utf-8')
        return b"%PDF-1.4\n1 0 obj<<>>endobj\nstream\n" + content + b"\nendstream\n%%EOF"
