import { serve } from "https://deno.land/std@0.177.0/http/server.ts"
import { jsPDF } from "https://esm.sh/jspdf@2.5.1"
import { corsHeaders } from "../_shared/cors.ts"

/**
 * generate-pdf
 * 
 * Genera un documento PDF para la representación gráfica de la
 * factura electrónica utilizando la librería jspdf en el runtime de Deno.
 */

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const { 
      invoice_number, 
      date, 
      issuer_name, 
      client_name, 
      items, 
      total 
    } = await req.json()

    // 1. Inicialización de documento PDF (A4)
    const doc = new jsPDF()

    // 2. Diseño de Cabecera
    doc.setFontSize(22)
    doc.text("ZONA SUR TECH - FACTURA CR", 20, 20)
    
    doc.setFontSize(10)
    doc.text(`Documento #: ${invoice_number}`, 20, 30)
    doc.text(`Fecha: ${date}`, 20, 35)
    doc.text(`Emisor: ${issuer_name}`, 20, 40)
    doc.text(`Cliente: ${client_name}`, 20, 45)

    // 3. Tabla de Ítems (Simplificada)
    doc.setLineWidth(0.5)
    doc.line(20, 55, 190, 55)
    doc.text("Descripción", 25, 62)
    doc.text("Cantidad", 120, 62)
    doc.text("Monto", 160, 62)
    doc.line(20, 65, 190, 65)

    let y = 72
    if (items && Array.isArray(items)) {
      items.forEach((item: any) => {
        doc.text(item.description || "Sin descripción", 25, y)
        doc.text(String(item.quantity || 1), 125, y)
        doc.text(String(item.total || 0), 165, y)
        y += 7
      })
    }

    // 4. Totales
    doc.setFontSize(14)
    doc.text(`TOTAL FACTURA: ${total} CRC`, 20, y + 20)

    // 5. Pie de página
    doc.setFontSize(8)
    doc.text("Este documento es una representación gráfica de un comprobante electrónico.", 20, 280)

    // 6. Generación de ArrayBuffer
    const pdfOutput = doc.output('arraybuffer')

    return new Response(pdfOutput, {
      headers: { 
        ...corsHeaders, 
        'Content-Type': 'application/pdf',
        'Content-Disposition': `attachment; filename="factura-${invoice_number}.pdf"`
      },
      status: 200,
    })

  } catch (error) {
    console.error(`Error generando PDF: ${error.message}`)
    return new Response(JSON.stringify({ error: error.message }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      status: 400,
    })
  }
})
