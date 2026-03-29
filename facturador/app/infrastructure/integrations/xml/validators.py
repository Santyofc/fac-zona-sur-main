import xml.etree.ElementTree as ET


def validate_xml_structure(xml_content: str) -> None:
    root = ET.fromstring(xml_content.encode('utf-8'))
    required = {'Clave', 'NumeroConsecutivo', 'FechaEmision', 'DetalleServicio'}
    tags = {el.tag.split('}')[-1] for el in root.iter()}
    missing = required.difference(tags)
    if missing:
        raise ValueError(f'XML missing required tags: {missing}')
