import { serve } from "https://deno.land/std@0.177.0/http/server.ts"
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.7.1"
import Stripe from 'https://esm.sh/stripe@11.16.0?target=deno'
import { corsHeaders } from "../_shared/cors.ts"

/**
 * stripe-webhook
 * 
 * Gestiona eventos de facturación y suscripciones de Stripe para
 * mantener sincronizado el estado del tenant en la base de datos local.
 */

const stripe = new Stripe(Deno.env.get('STRIPE_SECRET_KEY') ?? '', {
  apiVersion: '2022-11-15',
  httpClient: Stripe.createFetchHttpClient(),
})

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const signature = req.headers.get('stripe-signature')
    if (!signature) throw new Error('Missing stripe-signature')

    const body = await req.text()
    const webhookSecret = Deno.env.get('STRIPE_WEBHOOK_SECRET') ?? ''
    
    // Verificación de la firma del Webhook
    let event
    try {
      event = await stripe.webhooks.constructEventAsync(body, signature, webhookSecret)
    } catch (err) {
      console.error(`Invalid signature: ${err.message}`)
      return new Response(JSON.stringify({ error: 'Invalid Webhook Signature' }), { status: 400 })
    }

    // Inicialización de Supabase con Service Role
    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    )

    console.log(`Processing event: ${event.type}`)

    // Manejo de eventos específicos
    switch (event.type) {
      case 'checkout.session.completed': {
        const session = event.data.object
        const customerId = session.customer as string
        const userEmail = session.customer_details?.email
        
        // Actualizar suscripción del usuario
        const { error } = await supabaseClient
          .from('subscriptions')
          .upsert({
            stripe_customer_id: customerId,
            status: 'active',
            email: userEmail,
            plan_id: session.metadata?.plan_id,
            updated_at: new Date().toISOString()
          })
        
        if (error) throw error
        break
      }
      
      case 'customer.subscription.deleted': {
        const subscription = event.data.object
        const { error } = await supabaseClient
          .from('subscriptions')
          .update({ status: 'canceled', updated_at: new Date().toISOString() })
          .eq('stripe_subscription_id', subscription.id)
        
        if (error) throw error
        break
      }
    }

    return new Response(JSON.stringify({ received: true }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      status: 200,
    })

  } catch (error) {
    return new Response(JSON.stringify({ error: error.message }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      status: 400,
    })
  }
})
