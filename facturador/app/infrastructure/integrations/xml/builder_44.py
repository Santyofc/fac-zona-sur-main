import xml.etree.ElementTree as ET


class XML44Builder:
    async def build(self, payload: dict) -> str:
        ns = 'https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/facturaElectronica'
        root_tag = {
            'FE': 'FacturaElectronica',
            'TE': 'TiqueteElectronico',
            'NC': 'NotaCreditoElectronica',
            'ND': 'NotaDebitoElectronica',
        }[payload['doc_type']]
        root = ET.Element(f'{{{ns}}}{root_tag}')

        ET.SubElement(root, 'Clave').text = payload.get('clave') or 'PENDING'
        ET.SubElement(root, 'NumeroConsecutivo').text = payload.get('consecutive') or 'PENDING'
        ET.SubElement(root, 'FechaEmision').text = payload.get('issue_date').isoformat()

        emisor = ET.SubElement(root, 'Emisor')
        ET.SubElement(emisor, 'Nombre').text = payload.get('issuer_name', 'Emisor')

        detalle = ET.SubElement(root, 'DetalleServicio')
        for idx, item in enumerate(payload['items'], start=1):
            line = ET.SubElement(detalle, 'LineaDetalle')
            ET.SubElement(line, 'NumeroLinea').text = str(idx)
            ET.SubElement(line, 'Codigo').text = item.get('cabys_code', '0000000000000')
            ET.SubElement(line, 'Detalle').text = item['description']
            ET.SubElement(line, 'Cantidad').text = str(item['quantity'])
            ET.SubElement(line, 'PrecioUnitario').text = str(item['unit_price'])

        return ET.tostring(root, encoding='utf-8', xml_declaration=True).decode('utf-8')
