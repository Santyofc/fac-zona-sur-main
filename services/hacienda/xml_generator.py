"""
Generador de XML — Comprobantes Electrónicos Hacienda CR versión 4.4

Implementa los siguientes tipos de comprobante:
  - FacturaElectronica   (FE)  — 01
  - NotaDebitoElectronica (ND) — 02
  - NotaCreditoElectronica (NC)— 03
  - TiqueteElectronico   (TE)  — 04

Namespace raíz per Hacienda: https://cdn.comprobanteselectronicos.go.cr/xml/v4.4/facturaElectronica

Referencias:
  - Anexos y Estructuras v4.4 — Ministerio de Hacienda CR
  - https://www.hacienda.go.cr/docs/Anexosyestructuras.pdf
"""

from __future__ import annotations
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from xml.etree import ElementTree as ET
from typing import Optional
import xml.dom.minidom


# ─── Namespaces Oficiales Hacienda CR v4.4 ────────────────────────────────────
NS = {
    "fe":  "https://cdn.comprobanteselectronicos.go.cr/xml/v4.4/facturaElectronica",
    "nd":  "https://cdn.comprobanteselectronicos.go.cr/xml/v4.4/notaDebitoElectronica",
    "nc":  "https://cdn.comprobanteselectronicos.go.cr/xml/v4.4/notaCreditoElectronica",
    "te":  "https://cdn.comprobanteselectronicos.go.cr/xml/v4.4/tiqueteElectronico",
    "fee": "https://cdn.comprobanteselectronicos.go.cr/xml/v4.4/facturaElectronicaExportacion",
    "fec": "https://cdn.comprobanteselectronicos.go.cr/xml/v4.4/facturaElectronicaCompra",
    "xsd": "http://www.w3.org/2001/XMLSchema",
    "ds":  "http://www.w3.org/2000/09/xmldsig#",
}

# Root element names
ROOT_NAMES = {
    "FE": "FacturaElectronica",
    "ND": "NotaDebitoElectronica",
    "NC": "NotaCreditoElectronica",
    "TE": "TiqueteElectronico",
    "FEE": "FacturaElectronicaExportacion",
    "FEC": "FacturaElectronicaCompra",
}

# Normativa
NORMATIVA_NUM    = "v4.4"
NORMATIVA_FECHA  = "10-08-2023"


def _d(value, precision="0.01") -> Decimal:
    """Convierte a Decimal con redondeo HALF_UP a 2 decimales."""
    return Decimal(str(value)).quantize(Decimal(precision), rounding=ROUND_HALF_UP)


def _d5(value) -> Decimal:
    """Decimal con 5 posiciones para cantidades y precios."""
    return Decimal(str(value)).quantize(Decimal("0.00001"), rounding=ROUND_HALF_UP)


def _sub(parent: ET.Element, tag: str, text: str | None = None, **attrs) -> ET.Element:
    """Crea un sub-elemento con texto y atributos opcionales."""
    el = ET.SubElement(parent, tag, **attrs)
    if text is not None:
        el.text = str(text)
    return el


# ─── Builder de Emisor / Receptor ─────────────────────────────────────────────
def _build_emisor(parent: ET.Element, emisor: dict) -> None:
    """
    Construye la sección <Emisor>.
    emisor: {nombre, tipo_cedula, cedula, nombre_comercial?, ubicacion?, correo, telefono?}
    """
    em = _sub(parent, "Emisor")
    _sub(em, "Nombre", emisor["nombre"])
    if emisor.get("nombre_comercial"):
        _sub(em, "NombreComercial", emisor["nombre_comercial"])
    cedula_el = _sub(em, "Identificacion")
    _sub(cedula_el, "Tipo", _cedula_type_code(emisor.get("tipo_cedula", "JURIDICA")))
    _sub(cedula_el, "Numero", emisor["cedula"].zfill(12 if emisor.get("tipo_cedula", "JURIDICA") != "FISICA" else 9))
    # Ubicación
    if ub := emisor.get("ubicacion"):
        _build_ubicacion(em, ub)
    if emiror_tel := emisor.get("telefono"):
        _build_telefono(em, emiror_tel)
    _sub(em, "CorreoElectronico", emisor["correo"])


def _build_receptor(parent: ET.Element, receptor: dict | None) -> None:
    """
    Construye la sección <Receptor> (opcional en tiquetes).
    receptor: {nombre, tipo_cedula, cedula, correo?, ubicacion?, telefono?}
    """
    if not receptor:
        return
    rc = _sub(parent, "Receptor")
    _sub(rc, "Nombre", receptor["nombre"])
    if ced := receptor.get("cedula"):
        cedula_el = _sub(rc, "Identificacion")
        _sub(cedula_el, "Tipo", _cedula_type_code(receptor.get("tipo_cedula", "FISICA")))
        _sub(cedula_el, "Numero", ced)
    if ub := receptor.get("ubicacion"):
        _build_ubicacion(rc, ub)
    if tel := receptor.get("telefono"):
        _build_telefono(rc, tel)
    if correo := receptor.get("correo"):
        _sub(rc, "CorreoElectronico", correo)


def _build_ubicacion(parent: ET.Element, ubicacion: dict) -> None:
    """Construye <Ubicacion>."""
    ub = _sub(parent, "Ubicacion")
    if provinica := ubicacion.get("provincia"):
        _sub(ub, "Provincia", provinica)
    if canton := ubicacion.get("canton"):
        _sub(ub, "Canton", canton)
    if distrito := ubicacion.get("distrito"):
        _sub(ub, "Distrito", distrito)
    if barrio := ubicacion.get("barrio"):
        _sub(ub, "Barrio", barrio)
    if otras := ubicacion.get("otras_senas"):
        _sub(ub, "OtrasSenas", otras)
    if otras_ext := ubicacion.get("otras_senas_extranjero"):
        _sub(ub, "OtrasSenasExtranjero", otras_ext)


def _build_telefono(parent: ET.Element, telefono: dict | str) -> None:
    """Construye <Telefono>."""
    tel_el = _sub(parent, "Telefono")
    if isinstance(telefono, dict):
        _sub(tel_el, "CodigoPais", telefono.get("codigo_pais", "506"))
        _sub(tel_el, "NumTelefono", telefono.get("numero", ""))
    else:
        _sub(tel_el, "CodigoPais", "506")
        _sub(tel_el, "NumTelefono", str(telefono))


def _cedula_type_code(tipo: str) -> str:
    """Mapea tipo cédula a código Hacienda."""
    mapping = {
        "FISICA":     "01",
        "JURIDICA":   "02",
        "DIMEX":      "03",
        "NITE":       "04",
        "EXTRANJERO": "05",
    }
    return mapping.get(tipo.upper(), "02")


# ─── Detalle de Servicios / Líneas ────────────────────────────────────────────
def _build_detalle_servicio(parent: ET.Element, items: list[dict]) -> None:
    """
    Construye <DetalleServicio> con todas sus <LineaDetalle>.

    Cada item:
    {
      linea_numero: int,
      cabys_code: str,
      descripcion: str,
      cantidad: float,
      unidad_medida: str,   # "Unid", "Sp", "Os", etc.
      precio_unitario: float,
      descuento_porcentaje: float,  # 0-100
      impuesto_codigo: str,         # "01" = IVA, "07" = tarifa cero
      impuesto_tarifa_codigo: str,  # "08" = 13%, "04" = 4%, "02" = 1%, "01" = 0%
      impuesto_tarifa: float,       # porcentaje: 13, 8, 4, 2, 1, 0
    }
    """
    ds = _sub(parent, "DetalleServicio")

    for item in items:
        ld = _sub(ds, "LineaDetalle")
        _sub(ld, "NumeroLinea", str(item["linea_numero"]))
        _sub(ld, "CodigoCabys", item["cabys_code"])

        # Código comercial (opcional)
        if cod := item.get("codigo_comercial"):
            cc = _sub(ld, "CodigoComercial")
            _sub(cc, "Tipo", cod.get("tipo", "04"))  # 04 = código interno
            _sub(cc, "Codigo", cod["codigo"])

        _sub(ld, "Cantidad", float_str(item["cantidad"], 5))
        _sub(ld, "UnidadMedida", item.get("unidad_medida", "Unid"))
        if detalle := item.get("detalle"):
            _sub(ld, "Detalle", detalle)
        _sub(ld, "PrecioUnitario", float_str(item["precio_unitario"], 5))

        # Calcular subtotal base
        cantidad   = _d5(item["cantidad"])
        precio_u   = _d5(item["precio_unitario"])
        subtotal   = (cantidad * precio_u).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        _sub(ld, "MontoTotal", str(subtotal))

        # Descuentos
        descuento_total = Decimal("0.00")
        if item.get("descuento_porcentaje", 0) > 0:
            desc_pct   = _d(item["descuento_porcentaje"]) / 100
            desc_amt   = (subtotal * desc_pct).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            disc_block = _sub(ld, "Descuento")
            _sub(disc_block, "MontoDescuento", str(desc_amt))
            if nat := item.get("naturaleza_descuento"):
                _sub(disc_block, "NaturalezaDescuento", nat)
            descuento_total += desc_amt

        subtotal_posimp = subtotal - descuento_total
        _sub(ld, "SubTotal", str(subtotal_posimp))

        # Impuesto (IVA)
        impuesto_monto = Decimal("0.00")
        if item.get("impuesto_codigo") and item.get("impuesto_tarifa_codigo"):
            imp = _sub(ld, "Impuesto")
            _sub(imp, "Codigo", item["impuesto_codigo"])           # 01 = IVA
            _sub(imp, "CodigoTarifa", item["impuesto_tarifa_codigo"])  # 08 = 13%
            _sub(imp, "Tarifa", float_str(item.get("impuesto_tarifa", 0), 2))
            impuesto_monto = (subtotal_posimp * _d(item.get("impuesto_tarifa", 0)) / 100).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP)
            _sub(imp, "Monto", str(impuesto_monto))

        total_linea = subtotal_posimp + impuesto_monto
        _sub(ld, "MontoTotalLinea", str(total_linea))


def _build_resumen(parent: ET.Element, items: list[dict], currency: str = "CRC",
                   exchange_rate: float = 1.0) -> dict:
    """
    Construye <ResumenFactura> y retorna los totales calculados.
    """
    totals = _calculate_totals(items)
    rf = _sub(parent, "ResumenFactura")
    if currency != "CRC":
        _sub(rf, "CodigoTipoMoneda")
        cod_mon = ET.SubElement(rf, "CodigoTipoMoneda")
        _sub(cod_mon, "CodigoMoneda", currency)
        _sub(cod_mon, "TipoCambio", float_str(exchange_rate, 5))
    _sub(rf, "TotalServGravados",     str(totals["total_serv_gravados"]))
    _sub(rf, "TotalServExentos",      str(totals["total_serv_exentos"]))
    _sub(rf, "TotalServExonerado",    str(totals["total_serv_exonerado"]))
    _sub(rf, "TotalMercanciasGravadas", str(totals["total_merc_gravadas"]))
    _sub(rf, "TotalMercanciasExentas",  str(totals["total_merc_exentas"]))
    _sub(rf, "TotalMercExonerada",    str(totals["total_merc_exonerada"]))
    _sub(rf, "TotalGravado",          str(totals["total_gravado"]))
    _sub(rf, "TotalExento",           str(totals["total_exento"]))
    _sub(rf, "TotalExonerado",        str(totals["total_exonerado"]))
    _sub(rf, "TotalVenta",            str(totals["total_venta"]))
    _sub(rf, "TotalDescuentos",       str(totals["total_descuentos"]))
    _sub(rf, "TotalVentaNeta",        str(totals["total_venta_neta"]))
    _sub(rf, "TotalImpuesto",         str(totals["total_impuesto"]))
    _sub(rf, "TotalComprobante",      str(totals["total_comprobante"]))
    return totals


def _calculate_totals(items: list[dict]) -> dict:
    """Calcula los totales del resumen de factura."""
    total_serv_gravados: Decimal     = Decimal("0.00")
    total_serv_exentos: Decimal      = Decimal("0.00")
    total_serv_exonerado: Decimal    = Decimal("0.00")
    total_merc_gravadas: Decimal     = Decimal("0.00")
    total_merc_exentas: Decimal      = Decimal("0.00")
    total_merc_exonerada: Decimal    = Decimal("0.00")
    total_descuentos: Decimal        = Decimal("0.00")
    total_impuesto: Decimal          = Decimal("0.00")

    for item in items:
        cantidad = _d5(item["cantidad"])
        precio_u = _d5(item["precio_unitario"])
        subtotal = (cantidad * precio_u).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        desc_pct = _d(item.get("descuento_porcentaje", 0)) / 100
        desc_amt = (subtotal * desc_pct).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total_descuentos = Decimal(total_descuentos) + Decimal(desc_amt)

        subtotal_neto = subtotal - desc_amt
        tarifa = _d(item.get("impuesto_tarifa", 0))
        imp_monto = (subtotal_neto * tarifa / 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total_impuesto = Decimal(total_impuesto) + Decimal(imp_monto)

        # Clasificar servicio vs mercancía y gravado vs exento
        is_service   = item.get("unidad_medida", "Unid") in ("Sp", "Os", "Spe", "St", "Al")
        is_exento    = tarifa == Decimal("0.00")
        is_exonerado = item.get("exonerado", False)

        if is_exonerado:
            if is_service:
                total_serv_exonerado = Decimal(total_serv_exonerado) + Decimal(subtotal_neto)
            else:
                total_merc_exonerada = Decimal(total_merc_exonerada) + Decimal(subtotal_neto)
        elif is_exento:
            if is_service:
                total_serv_exentos = Decimal(total_serv_exentos) + Decimal(subtotal_neto)
            else:
                total_merc_exentas = Decimal(total_merc_exentas) + Decimal(subtotal_neto)
        else:
            if is_service:
                total_serv_gravados = Decimal(total_serv_gravados) + Decimal(subtotal_neto)
            else:
                total_merc_gravadas = Decimal(total_merc_gravadas) + Decimal(subtotal_neto)

    total_gravado   = Decimal(total_serv_gravados) + Decimal(total_merc_gravadas)
    total_exento    = Decimal(total_serv_exentos)  + Decimal(total_merc_exentas)
    total_exonerado = Decimal(total_serv_exonerado) + Decimal(total_merc_exonerada)
    total_venta     = Decimal(total_gravado) + Decimal(total_exento) + Decimal(total_exonerado) + Decimal(total_descuentos)
    total_venta_neta = Decimal(total_venta) - Decimal(total_descuentos)
    total_comprobante = Decimal(total_venta_neta) + Decimal(total_impuesto)

    return {
        "total_serv_gravados":  total_serv_gravados,
        "total_serv_exentos":   total_serv_exentos,
        "total_serv_exonerado": total_serv_exonerado,
        "total_merc_gravadas":  total_merc_gravadas,
        "total_merc_exentas":   total_merc_exentas,
        "total_merc_exonerada": total_merc_exonerada,
        "total_gravado":        total_gravado,
        "total_exento":         total_exento,
        "total_exonerado":      total_exonerado,
        "total_venta":          total_venta,
        "total_descuentos":     total_descuentos,
        "total_venta_neta":     total_venta_neta,
        "total_impuesto":       total_impuesto,
        "total_comprobante":    total_comprobante,
    }


def float_str(value, decimals: int = 2) -> str:
    """Formatea un número con N decimales (sin trailing zeros en Hacienda: usa el mínimo necesario)."""
    d = Decimal(str(value)).quantize(Decimal(f"0.{'0' * decimals}"), rounding=ROUND_HALF_UP)
    return str(d)


# ─── Generador Principal ──────────────────────────────────────────────────────
def generate_xml(payload: dict) -> str:
    """
    Genera el XML completo de un comprobante electrónico según Hacienda CR v4.4.

    Args:
        payload: Diccionario con todos los datos de la factura. Estructura:
        {
          "doc_type": "FE" | "ND" | "NC" | "TE",
          "clave": str,           # 50 dígitos
          "consecutivo": str,     # 20 dígitos
          "fecha_emision": str,   # ISO 8601 con zona horaria: "2024-01-15T10:30:00-06:00"
          "emisor": {...},
          "receptor": {...},     # None para tiquetes
          "condicion_venta": str, # "01"=Contado, "02"=Crédito, etc.
          "plazo_credito": str,   # Solo si condicion_venta="02"
          "medio_pago": list[str],# ["01"]=Efectivo, ["02"]=Tarjeta, etc.
          "moneda": str,          # "CRC" | "USD"
          "tipo_cambio": float,   # 1.0 para CRC
          "items": [...],
          "informacion_referencia": [...]  # Para NC/ND
          "otros": str,           # Información adicional
        }

    Returns:
        String XML minificado/pretty-printed según estándar Hacienda.
    """
    doc_type = payload.get("doc_type", "FE")
    ns_uri   = NS[doc_type.lower()]
    root_tag = ROOT_NAMES[doc_type]

    # Registrar namespaces
    ET.register_namespace("",    ns_uri)
    ET.register_namespace("xsd", NS["xsd"])
    ET.register_namespace("ds",  NS["ds"])

    # Root element con atributos de schema
    root = ET.Element(
        f"{{{ns_uri}}}{root_tag}",
        attrib={
            "xmlns:xsd":          NS["xsd"],
            "xmlns:ds":           NS["ds"],
        }
    )

    # ─── Campos obligatorios ─────────────────────────────────
    _sub(root, f"{{{ns_uri}}}Clave",             payload["clave"])
    _sub(root, f"{{{ns_uri}}}CodigoActividad",   payload.get("codigo_actividad", "722000"))
    _sub(root, f"{{{ns_uri}}}NumeroConsecutivo",  payload["consecutivo"])
    _sub(root, f"{{{ns_uri}}}FechaEmision",       payload["fecha_emision"])

    # ─── Emisor ──────────────────────────────────────────────
    emisor_el = ET.SubElement(root, f"{{{ns_uri}}}Emisor")
    emisor    = payload["emisor"]
    _sub(emisor_el, f"{{{ns_uri}}}Nombre", emisor["nombre"])
    if nc := emisor.get("nombre_comercial"):
        _sub(emisor_el, f"{{{ns_uri}}}NombreComercial", nc)
    ident_em = ET.SubElement(emisor_el, f"{{{ns_uri}}}Identificacion")
    _sub(ident_em, f"{{{ns_uri}}}Tipo",   _cedula_type_code(emisor.get("tipo_cedula", "JURIDICA")))
    _sub(ident_em, f"{{{ns_uri}}}Numero", "".join(filter(str.isdigit, emisor["cedula"])))

    if ub := emisor.get("ubicacion"):
        ub_el = ET.SubElement(emisor_el, f"{{{ns_uri}}}Ubicacion")
        if prov   := ub.get("provincia"):  _sub(ub_el, f"{{{ns_uri}}}Provincia", prov)
        if canton := ub.get("canton"):     _sub(ub_el, f"{{{ns_uri}}}Canton",    canton)
        if dist   := ub.get("distrito"):   _sub(ub_el, f"{{{ns_uri}}}Distrito",  dist)
        if barrio := ub.get("barrio"):     _sub(ub_el, f"{{{ns_uri}}}Barrio",    barrio)
        if otras  := ub.get("otras_senas"): _sub(ub_el, f"{{{ns_uri}}}OtrasSenas", otras)

    if tel := emisor.get("telefono"):
        tel_el = ET.SubElement(emisor_el, f"{{{ns_uri}}}Telefono")
        _sub(tel_el, f"{{{ns_uri}}}CodigoPais",   tel.get("codigo_pais", "506") if isinstance(tel, dict) else "506")
        _sub(tel_el, f"{{{ns_uri}}}NumTelefono",  tel.get("numero", str(tel)) if isinstance(tel, dict) else str(tel))

    _sub(emisor_el, f"{{{ns_uri}}}CorreoElectronico", emisor["correo"])

    # ─── Receptor (opcional en TE) ───────────────────────────
    receptor = payload.get("receptor")
    if receptor and doc_type != "TE":
        rec_el = ET.SubElement(root, f"{{{ns_uri}}}Receptor")
        _sub(rec_el, f"{{{ns_uri}}}Nombre", receptor["nombre"])
        if ced := receptor.get("cedula"):
            ident_rc = ET.SubElement(rec_el, f"{{{ns_uri}}}Identificacion")
            _sub(ident_rc, f"{{{ns_uri}}}Tipo",   _cedula_type_code(receptor.get("tipo_cedula", "FISICA")))
            _sub(ident_rc, f"{{{ns_uri}}}Numero", "".join(filter(str.isdigit, ced)))
        if ub := receptor.get("ubicacion"):
            ub_el = ET.SubElement(rec_el, f"{{{ns_uri}}}Ubicacion")
            if prov   := ub.get("provincia"):   _sub(ub_el, f"{{{ns_uri}}}Provincia",   prov)
            if canton := ub.get("canton"):      _sub(ub_el, f"{{{ns_uri}}}Canton",      canton)
            if dist   := ub.get("distrito"):    _sub(ub_el, f"{{{ns_uri}}}Distrito",    dist)
            if otras  := ub.get("otras_senas"): _sub(ub_el, f"{{{ns_uri}}}OtrasSenas",  otras)
        if correo := receptor.get("correo"):
            _sub(rec_el, f"{{{ns_uri}}}CorreoElectronico", correo)

    # ─── Condición de venta / Medio de pago ─────────────────
    _sub(root, f"{{{ns_uri}}}CondicionVenta", payload.get("condicion_venta", "01"))
    if payload.get("plazo_credito"):
        _sub(root, f"{{{ns_uri}}}PlazoCredito", str(payload["plazo_credito"]))

    medios = payload.get("medio_pago", ["01"])
    for medio in (medios if isinstance(medios, list) else [medios]):
        _sub(root, f"{{{ns_uri}}}MedioPago", str(medio))

    # ─── Detalle de servicios ─────────────────────────────────
    items   = payload.get("items", [])
    ds_el   = ET.SubElement(root, f"{{{ns_uri}}}DetalleServicio")

    for item in items:
        ld = ET.SubElement(ds_el, f"{{{ns_uri}}}LineaDetalle")
        _sub(ld, f"{{{ns_uri}}}NumeroLinea",   str(item["linea_numero"]))
        _sub(ld, f"{{{ns_uri}}}CodigoCabys",   item["cabys_code"])
        if cod := item.get("codigo_comercial"):
            cc = ET.SubElement(ld, f"{{{ns_uri}}}CodigoComercial")
            _sub(cc, f"{{{ns_uri}}}Tipo",   cod.get("tipo", "04"))
            _sub(cc, f"{{{ns_uri}}}Codigo", cod["codigo"])
        _sub(ld, f"{{{ns_uri}}}Cantidad",      float_str(item["cantidad"], 3))
        _sub(ld, f"{{{ns_uri}}}UnidadMedida",  item.get("unidad_medida", "Unid"))
        if det := item.get("detalle"):
            _sub(ld, f"{{{ns_uri}}}Detalle", det)
        _sub(ld, f"{{{ns_uri}}}PrecioUnitario", float_str(item["precio_unitario"], 5))

        cant     = _d5(item["cantidad"])
        precio   = _d5(item["precio_unitario"])
        total_   = (cant * precio).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        _sub(ld, f"{{{ns_uri}}}MontoTotal", str(total_))

        desc_pct = _d(item.get("descuento_porcentaje", 0)) / 100
        desc_amt = (total_ * desc_pct).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if desc_amt > 0:
            disc = ET.SubElement(ld, f"{{{ns_uri}}}Descuento")
            _sub(disc, f"{{{ns_uri}}}MontoDescuento", str(desc_amt))
            _sub(disc, f"{{{ns_uri}}}NaturalezaDescuento", item.get("naturaleza_descuento", "Descuento comercial"))

        subtotal_neto = total_ - desc_amt
        _sub(ld, f"{{{ns_uri}}}SubTotal", str(subtotal_neto))

        tarifa = _d(item.get("impuesto_tarifa", 13))
        if item.get("impuesto_codigo"):
            imp_el = ET.SubElement(ld, f"{{{ns_uri}}}Impuesto")
            _sub(imp_el, f"{{{ns_uri}}}Codigo",       item["impuesto_codigo"])
            _sub(imp_el, f"{{{ns_uri}}}CodigoTarifa", item["impuesto_tarifa_codigo"])
            _sub(imp_el, f"{{{ns_uri}}}Tarifa",       float_str(tarifa, 2))
            imp_monto = (subtotal_neto * tarifa / 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            _sub(imp_el, f"{{{ns_uri}}}Monto", str(imp_monto))
        else:
            imp_monto = Decimal("0.00")

        total_linea = subtotal_neto + imp_monto
        _sub(ld, f"{{{ns_uri}}}MontoTotalLinea", str(total_linea))

    # ─── Resumen ──────────────────────────────────────────────
    totals = _calculate_totals(items)
    rf     = ET.SubElement(root, f"{{{ns_uri}}}ResumenFactura")

    # Moneda extranjera
    moneda = payload.get("moneda", "CRC")
    if moneda != "CRC":
        cod_mon = ET.SubElement(rf, f"{{{ns_uri}}}CodigoTipoMoneda")
        _sub(cod_mon, f"{{{ns_uri}}}CodigoMoneda", moneda)
        _sub(cod_mon, f"{{{ns_uri}}}TipoCambio",   float_str(payload.get("tipo_cambio", 1.0), 5))

    _sub(rf, f"{{{ns_uri}}}TotalServGravados",      str(totals["total_serv_gravados"]))
    _sub(rf, f"{{{ns_uri}}}TotalServExentos",       str(totals["total_serv_exentos"]))
    _sub(rf, f"{{{ns_uri}}}TotalServExonerado",     str(totals["total_serv_exonerado"]))
    _sub(rf, f"{{{ns_uri}}}TotalMercanciasGravadas", str(totals["total_merc_gravadas"]))
    _sub(rf, f"{{{ns_uri}}}TotalMercanciasExentas",  str(totals["total_merc_exentas"]))
    _sub(rf, f"{{{ns_uri}}}TotalMercExonerada",     str(totals["total_merc_exonerada"]))
    _sub(rf, f"{{{ns_uri}}}TotalGravado",           str(totals["total_gravado"]))
    _sub(rf, f"{{{ns_uri}}}TotalExento",            str(totals["total_exento"]))
    _sub(rf, f"{{{ns_uri}}}TotalExonerado",         str(totals["total_exonerado"]))
    _sub(rf, f"{{{ns_uri}}}TotalVenta",             str(totals["total_venta"]))
    _sub(rf, f"{{{ns_uri}}}TotalDescuentos",        str(totals["total_descuentos"]))
    _sub(rf, f"{{{ns_uri}}}TotalVentaNeta",         str(totals["total_venta_neta"]))
    _sub(rf, f"{{{ns_uri}}}TotalImpuesto",          str(totals["total_impuesto"]))
    _sub(rf, f"{{{ns_uri}}}TotalComprobante",       str(totals["total_comprobante"]))

    # ─── Información de Referencia (NC/ND) ────────────────────
    for ref in payload.get("informacion_referencia", []):
        ref_el = ET.SubElement(root, f"{{{ns_uri}}}InformacionReferencia")
        _sub(ref_el, f"{{{ns_uri}}}TipoDoc",     ref.get("tipo_doc", "01"))
        _sub(ref_el, f"{{{ns_uri}}}Numero",      ref["numero"])
        _sub(ref_el, f"{{{ns_uri}}}FechaEmision", ref["fecha_emision"])
        _sub(ref_el, f"{{{ns_uri}}}Codigo",      ref.get("codigo", "01"))
        if razon := ref.get("razon"):
            _sub(ref_el, f"{{{ns_uri}}}Razon", razon)

    # ─── Otros (texto libre) ─────────────────────────────────
    if otros := payload.get("otros"):
        otros_el = ET.SubElement(root, f"{{{ns_uri}}}Otros")
        _sub(otros_el, f"{{{ns_uri}}}OtroTexto", str(otros))

    # ─── Normativa (obligatorio) ─────────────────────────────
    norm = ET.SubElement(root, f"{{{ns_uri}}}Normativa")
    _sub(norm, f"{{{ns_uri}}}NumeroResolucion", NORMATIVA_NUM)
    _sub(norm, f"{{{ns_uri}}}FechaResolucion",   NORMATIVA_FECHA)

    # Serializar a string con pretty print
    raw_xml = ET.tostring(root, encoding="unicode", xml_declaration=False)
    pretty  = xml.dom.minidom.parseString(
        f'<?xml version="1.0" encoding="UTF-8"?>{raw_xml}'
    ).toprettyxml(indent="  ", encoding=None)

    # Remover la primera línea duplicada del XML declaration
    lines = pretty.split("\n")
    if lines[0].startswith("<?xml"):
        pass  # Ya está incluida
    return pretty
