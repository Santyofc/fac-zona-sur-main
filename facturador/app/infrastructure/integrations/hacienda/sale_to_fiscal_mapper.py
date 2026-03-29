from dataclasses import dataclass


@dataclass
class SaleToFiscalDocumentMapper:
    def map_sale(self, sale: dict, doc_type: str) -> dict:
        return {
            'doc_type': doc_type,
            'customer_id': sale.get('customer_id'),
            'currency': sale.get('currency', 'CRC'),
            'items': sale['items'],
            'notes': sale.get('notes'),
        }
