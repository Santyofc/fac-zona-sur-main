import { serve } from "https://deno.land/std@0.177.0/http/server.ts"
import { corsHeaders } from "../_shared/cors.ts"

/**
 * send-invoice-hacienda
 * 
 * Orquestador principal para la comunicación con el API de Hacienda CR.
 * 1. Obtiene token de acceso (OAuth2).
 * 2. Prepara el payload JSON con el XML firmado.
 * 3. Realiza el POST al endpoint de recepción.
 * 4. Retorna el estado inmediato del envío.
 */

const HACIENDA_AUTH_URL = "https://idp.comprobanteselectronicos.go.cr/auth/realms/rut-stag/protocol/openid-connect/token"
const HACIENDA_RECEPCION_URL = "https://api.comprobanteselectronicos.go.cr/recepcion-sandbox/v1/recepcion"

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const { 
      clave, 
      fecha, 
      emisor_numero, 
      receptor_numero, 
      comprobante_xml_base64,
      username,
      password
    } = await req.json()

    // 1. Obtención de Token OAuth2 para Hacienda
    const tokenResponse = await fetch(HACIENDA_AUTH_URL, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        grant_type: "password",
        client_id: "api-stag",
        username: username,
        password: password
      })
    })

    if (!tokenResponse.ok) throw new Error("Error obteniendo token de Hacienda.")
    const { access_token } = await tokenResponse.json()

    // 2. Construcción de Comprobante para Hacienda API
    const payload = {
      clave: clave,
      fecha: fecha,
      emisor: {
        tipoIdentificacion: emisor_numero.length === 9 ? "01" : "02",
        numeroIdentificacion: emisor_numero
      },
      receptor: receptor_numero ? {
        tipoIdentificacion: receptor_numero.length === 9 ? "01" : "02",
        numeroIdentificacion: receptor_numero
      } : undefined,
      comprobanteXml: comprobante_xml_base64
    }

    // 3. Envío del Documento
    const result = await fetch(HACIENDA_RECEPCION_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${access_token}`
      },
      body: JSON.stringify(payload)
    })

    const status = result.status
    const responseBody = await result.text()

    return new Response(JSON.stringify({
      status: status,
      api_response: responseBody,
      sent_at: new Date().toISOString()
    }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      status: status,
    })

  } catch (error) {
    console.error(`Error de orquestación Hacienda: ${error.message}`)
    return new Response(JSON.stringify({ error: error.message }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      status: 400,
    })
  }
})
