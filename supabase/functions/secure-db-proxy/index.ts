import { serve } from "https://deno.land/std@0.177.0/http/server.ts"
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.7.1"
import { corsHeaders } from "../_shared/cors.ts"

/**
 * secure-db-proxy
 * 
 * Este servicio actúa como un intermediario seguro para realizar operaciones
 * de base de datos que requieren validaciones de negocio complejas antes de ser
 * persistidas, saltándose RLS restrictivo cuando es estrictamente necesario 
 * bajo política de servidor.
 */

serve(async (req) => {
  // Manejo de Preflight (CORS)
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    // 1. Inicialización de cliente Supabase con Service Role (Elevated Privileges)
    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? '',
      { global: { headers: { Authorization: req.headers.get('Authorization')! } } }
    )

    // 2. Verificación de Usuario Autenticado
    const { data: { user }, error: authError } = await supabaseClient.auth.getUser()
    if (authError || !user) {
      return new Response(JSON.stringify({ error: 'Unauthorized User' }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 401,
      })
    }

    // 3. Procesamiento de Request
    const { table, action, payload } = await req.json()

    // 4. Lógica de Negocio / Guardián Seguro
    // Solo permitimos ciertas tablas y acciones seguras a través de este proxy
    const allowedTables = ['profiles', 'subscriptions', 'usage_metrics']
    if (!allowedTables.includes(table)) {
       throw new Error(`Insecure access attempt to table: ${table}`)
    }

    let result;
    if (action === 'get_secure_data') {
       const { data, error } = await supabaseClient
         .from(table)
         .select('*')
         .eq('user_id', user.id)
         .single()
       
       if (error) throw error
       result = data
    } else {
       throw new Error(`Action ${action} not implemented in secure proxy`)
    }

    return new Response(JSON.stringify({
      status: 'success',
      data: result,
      meta: { timestamp: new Date().toISOString(), node: Deno.hostname() }
    }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      status: 200,
    })

  } catch (error) {
    return new Response(JSON.stringify({ 
      error: error.message,
      code: 'INTERNAL_ERROR'
    }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      status: 400,
    })
  }
})
