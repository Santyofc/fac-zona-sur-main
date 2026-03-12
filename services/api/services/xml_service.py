"""
XML Generator — Genera el XML de factura electrónica según el
esquema FacturaElectrónica v4.3 del Ministerio de Hacienda de Costa Rica.

Referencia: https://www.hacienda.go.cr/ATV/ComprobanteElectronico/docs/
"""
from lxml import etree
from datetime import datetime
from decimal import Decimal


NAMESPACE = "https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.3/facturaElectronica"
XSD_URI = "https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.3/facturaElectronica FacturaElectronicaV4.3.xsd"


def _elem(parent: etree._Element, tag: str, text: str = None, **attrs) -> etree._Element:
    """Helper para crear elementos XML con namespace."""
    el = etree.SubElement(parent, f"{{{NAMESPACE}}}{tag}", **attrs)
    if text is not None:
        el.text = str(text)
    return el


def generate_invoice_xml(invoice, company) -> str:
    """
    Genera el XML de una FacturaElectrónica.

    Args:
        invoice: Instancia del modelo Invoice con items y cliente cargados
        company: Instancia del modelo Company

    Returns:
        String XML bien formado sin firmar
    """
    nsmap = {
        None: NAMESPACE,
        "xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "xsd": "http://www.w3.org/2001/XMLSchema",
        "ds": "http://www.w3.org/2000/09/xmldsig#",
    }

    root = etree.Element(f"{{{NAMESPACE}}}FacturaElectronica", nsmap=nsmap)
    root.set(
        "{http://www.w3.org/2001/XMLSchema-instance}schemaLocation",
        XSD_URI,
    )

    # ── Encabezado ─────────────────────────────────────────
    _elem(root, "Clave", invoice.clave)
    _elem(root, "CodigoActividad", company.economic_activity or "620900")
    _elem(root, "NumeroConsecutivo", invoice.consecutive)
    _elem(root, "FechaEmision", invoice.issue_date.strftime("%Y-%m-%dT%H:%M:%S-06:00"))

    # ── Emisor ─────────────────────────────────────────────
    emisor = _elem(root, "Emisor")
    _elem(emisor, "Nombre", company.name)
    identificacion_e = _elem(emisor, "Identificacion")
    _elem(identificacion_e, "Tipo", _map_cedula_type(company.cedula_type))
    _elem(identificacion_e, "Numero", "".join(filter(str.isdigit, company.cedula_number)))

    if company.phone:
        tel_e = _elem(emisor, "Telefono")
        _elem(tel_e, "CodigoPais", "506")
        _elem(tel_e, "NumTelefono", company.phone.replace("+506", "").replace(" ", "").replace("-", ""))

    _elem(emisor, "CorreoElectronico", company.email)

    ubi_e = _elem(emisor, "Ubicacion")
    _elem(ubi_e, "Provincia", _province_code(company.province or "San José"))
    _elem(ubi_e, "Canton", "01")
    _elem(ubi_e, "Distrito", "01")
    if company.address:
        _elem(ubi_e, "OtrasSenas", company.address)

    # ── Receptor ───────────────────────────────────────────
    if invoice.client:
        receptor = _elem(root, "Receptor")
        _elem(receptor, "Nombre", invoice.client.name)
        if invoice.client.cedula_number:
            identificacion_r = _elem(receptor, "Identificacion")
            _elem(identificacion_r, "Tipo", _map_cedula_type(invoice.client.cedula_type))
            _elem(identificacion_r, "Numero", "".join(filter(str.isdigit, invoice.client.cedula_number)))
        if invoice.client.email:
            _elem(receptor, "CorreoElectronico", invoice.client.email)

    # ── Condición y Medio de Pago ──────────────────────────
    _elem(root, "CondicionVenta", invoice.sale_condition)
    if invoice.sale_condition != "01":
        _elem(root, "PlazoCredito", str(invoice.credit_term_days or 0))

    medio_pago = _elem(root, "MedioPago")
    medio_pago.text = invoice.payment_method

    # ── Detalle de Servicios ───────────────────────────────
    detalle = _elem(root, "DetalleServicio")
    for item in sorted(invoice.items, key=lambda x: x.line_number):
        linea = _elem(detalle, "LineaDetalle")
        _elem(linea, "NumeroLinea", str(item.line_number))
        if item.cabys_code:
            _elem(linea, "CodigoCabys", item.cabys_code)
        _elem(linea, "Cantidad", _fmt(item.quantity))
        _elem(linea, "UnidadMedida", item.unit_measure)
        _elem(linea, "Detalle", item.description[:200])
        _elem(linea, "PrecioUnitario", _fmt(item.unit_price))

        if item.discount_pct and item.discount_pct > 0:
            descuento = _elem(linea, "Descuento")
            _elem(descuento, "MontoDescuento", _fmt(item.discount_amount))
            _elem(descuento, "NaturalezaDescuento", "Descuento comercial")

        _elem(linea, "SubTotal", _fmt(item.subtotal))

        impuesto = _elem(linea, "Impuesto")
        _elem(impuesto, "Codigo", "01")   # 01=IVA
        _elem(impuesto, "CodigoTarifa", _tax_rate_code(float(item.tax_rate)))
        _elem(impuesto, "Tarifa", _fmt(item.tax_rate))
        _elem(impuesto, "Monto", _fmt(item.tax_amount))

        _elem(linea, "MontoTotalLinea", _fmt(item.total))

    # ── Resumen Factura ────────────────────────────────────
    resumen = _elem(root, "ResumenFactura")
    _elem(resumen, "CodigoTipoMoneda")  # placeholder
    _elem(resumen, "TotalServGravados", _fmt(invoice.subtotal))
    _elem(resumen, "TotalServExentos", "0.00000")
    _elem(resumen, "TotalServExonerado", "0.00000")
    _elem(resumen, "TotalMercanciasGravadas", "0.00000")
    _elem(resumen, "TotalMercanciasExentas", "0.00000")
    _elem(resumen, "TotalMercExonerada", "0.00000")
    _elem(resumen, "TotalGravado", _fmt(invoice.subtotal))
    _elem(resumen, "TotalExento", "0.00000")
    _elem(resumen, "TotalExonerado", "0.00000")
    _elem(resumen, "TotalVenta", _fmt(invoice.subtotal))
    _elem(resumen, "TotalDescuentos", _fmt(invoice.discount_total))
    _elem(resumen, "TotalVentaNeta", _fmt(invoice.subtotal))
    _elem(resumen, "TotalImpuesto", _fmt(invoice.tax_total))
    _elem(resumen, "TotalComprobante", _fmt(invoice.total))

    return etree.tostring(root, pretty_print=True, xml_declaration=True, encoding="UTF-8").decode("utf-8")


# ─── Helpers ──────────────────────────────────────────────────

def _fmt(value) -> str:
    """Formatea un Decimal/float a 5 decimales."""
    return f"{Decimal(str(value)):.5f}"


def _map_cedula_type(cedula_type: str) -> str:
    """Mapea el tipo de cédula interno al código Hacienda."""
    mapping = {
        "FISICA": "01",
        "JURIDICA": "02",
        "DIMEX": "03",
        "NITE": "04",
        "EXTRANJERO": "05",
    }
    return mapping.get(cedula_type, "01")


def _province_code(province_name: str) -> str:
    """Retorna el código de provincia de Hacienda."""
    provinces = {
        "San José": "1", "Alajuela": "2", "Cartago": "3",
        "Heredia": "4", "Guanacaste": "5", "Puntarenas": "6", "Limón": "7",
    }
    return provinces.get(province_name, "1")


def _tax_rate_code(rate: float) -> str:
    """Retorna el código de tarifa IVA de Hacienda."""
    tariff_map = {0: "01", 1: "02", 2: "03", 4: "04", 8: "05", 13: "08"}
    return tariff_map.get(int(rate), "08")
