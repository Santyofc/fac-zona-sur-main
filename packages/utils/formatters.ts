/**
 * Factura CR — Shared Formatters
 * Utilidades de formateo para monedas, fechas y números de Costa Rica.
 */

/**
 * Formatea un número como moneda colones o dólares.
 */
export function formatCurrency(
  value: number | string,
  currency: 'CRC' | 'USD' = 'CRC',
  locale: string = 'es-CR'
): string {
  const num = typeof value === 'string' ? parseFloat(value) : value
  if (isNaN(num)) return '—'
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency,
    minimumFractionDigits: currency === 'CRC' ? 0 : 2,
    maximumFractionDigits: currency === 'CRC' ? 0 : 2,
  }).format(num)
}

/**
 * Formatea una fecha ISO a formato legible en es-CR.
 * @param date - ISO string o Date object
 * @param format - 'short' | 'long' | 'datetime'
 */
export function formatDate(
  date: string | Date,
  format: 'short' | 'long' | 'datetime' = 'short'
): string {
  const d = typeof date === 'string' ? new Date(date) : date
  if (isNaN(d.getTime())) return '—'

  const options: Intl.DateTimeFormatOptions =
    format === 'datetime'
      ? { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' }
      : format === 'long'
      ? { day: 'numeric', month: 'long', year: 'numeric' }
      : { day: '2-digit', month: 'short', year: 'numeric' }

  return new Intl.DateTimeFormat('es-CR', options).format(d)
}

/**
 * Formatea una cédula costarricense con guiones.
 * 1-2345-6789 (física) | 3-101-123456 (jurídica)
 */
export function formatCedula(cedula: string, type: string = 'FISICA'): string {
  const digits = cedula.replace(/\D/g, '')
  if (type === 'FISICA' && digits.length === 9) {
    return `${digits[0]}-${digits.slice(1, 5)}-${digits.slice(5)}`
  }
  if (type === 'JURIDICA' && digits.length === 10) {
    return `${digits[0]}-${digits.slice(1, 4)}-${digits.slice(4)}`
  }
  return cedula
}

/**
 * Trunca un string al máximo de caracteres con elipsis.
 */
export function truncate(str: string, maxLength: number = 30): string {
  if (!str) return ''
  return str.length > maxLength ? `${str.substring(0, maxLength)}...` : str
}

/**
 * Genera las iniciales de un nombre (para avatares).
 */
export function initials(name: string): string {
  return name
    .split(' ')
    .slice(0, 2)
    .map((n) => n.charAt(0).toUpperCase())
    .join('')
}
