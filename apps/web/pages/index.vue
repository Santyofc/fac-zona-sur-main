<template>
  <div>
    <!-- NAV -->
    <nav style="position: fixed; top: 0; width: 100%; z-index: 100; background: rgba(6,14,26,0.85); backdrop-filter: blur(12px); border-bottom: 1px solid rgba(37,99,235,0.12);">
      <div class="container" style="display: flex; justify-content: space-between; align-items: center; height: 60px;">
        <div style="display: flex; align-items: center; gap: 0.625rem;">
          <div style="width: 34px; height: 34px; background: linear-gradient(135deg,#2563EB,#1D4ED8); border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 1rem; font-weight: 800; color: white;">₡</div>
          <span style="font-weight: 800; font-size: 1.1rem; letter-spacing: -0.5px;">Factura CR</span>
          <span class="badge" style="background: rgba(37,99,235,0.15); color: #60A5FA; font-size: 0.65rem; margin-left: 4px;">v4.4</span>
        </div>
        <div style="display: flex; gap: 1.5rem; align-items: center;">
          <a href="#features" style="font-size: 0.875rem; color: var(--muted); text-decoration: none; transition: color 0.2s;" onmouseover="this.style.color='#F1F5F9'" onmouseout="this.style.color='#64748B'">Funciones</a>
          <a href="#pricing"  style="font-size: 0.875rem; color: var(--muted); text-decoration: none; transition: color 0.2s;" onmouseover="this.style.color='#F1F5F9'" onmouseout="this.style.color='#64748B'">Precios</a>
          <a href="http://localhost:3000" class="btn btn-primary" style="padding: 0.5rem 1rem; font-size: 0.8rem;">Acceder al Panel →</a>
        </div>
      </div>
    </nav>

    <!-- HERO -->
    <section style="min-height: 100vh; display: flex; align-items: center; padding: 80px 0 60px; position: relative; overflow: hidden;">
      <!-- Grid bg -->
      <div style="position: absolute; inset: 0; background-image: linear-gradient(rgba(37,99,235,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(37,99,235,0.04) 1px, transparent 1px); background-size: 40px 40px; pointer-events: none;"></div>
      <!-- Glow -->
      <div style="position: absolute; top: 20%; left: 50%; transform: translateX(-50%); width: 600px; height: 400px; background: radial-gradient(ellipse, rgba(37,99,235,0.12), transparent 70%); pointer-events: none;"></div>

      <div class="container" style="text-align: center; position: relative;">
        <div style="display: inline-flex; align-items: center; gap: 0.5rem; background: rgba(37,99,235,0.1); border: 1px solid rgba(37,99,235,0.25); border-radius: 20px; padding: 0.375rem 1rem; margin-bottom: 1.5rem; font-size: 0.8rem; color: #60A5FA;">
          ⚡ Comprobantes Electrónicos Hacienda CR v4.4
        </div>
        <h1 style="font-size: clamp(2.5rem, 5vw, 4rem); font-weight: 800; line-height: 1.1; letter-spacing: -1.5px; margin-bottom: 1.25rem; max-width: 800px; margin-left: auto; margin-right: auto;">
          Facturación electrónica
          <span style="background: linear-gradient(135deg, #2563EB, #06B6D4); -webkit-background-clip: text; -webkit-text-fill-color: transparent;"> para Costa Rica</span>
        </h1>
        <p style="font-size: 1.15rem; color: var(--muted); max-width: 560px; margin: 0 auto 2.5rem; line-height: 1.7;">
          Emite facturas electrónicas válidas para Hacienda CR en segundos. Firma digital XAdES, generación XML v4.4, envío automático y PDF con QR.
        </p>
        <div style="display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap;">
          <a href="http://localhost:3000" class="btn btn-primary" style="padding: 0.875rem 2rem; font-size: 1rem;">
            Comenzar gratis →
          </a>
          <a href="#features" class="btn btn-ghost" style="padding: 0.875rem 2rem; font-size: 1rem;">
            Ver funciones
          </a>
        </div>

        <!-- Stats strip -->
        <div style="display: flex; gap: 2.5rem; justify-content: center; margin-top: 4rem; flex-wrap: wrap;">
          <div v-for="s in stats" :key="s.label" style="text-align: center;">
            <div style="font-size: 1.75rem; font-weight: 800; color: #F1F5F9;">{{ s.value }}</div>
            <div style="font-size: 0.8rem; color: var(--muted); margin-top: 2px;">{{ s.label }}</div>
          </div>
        </div>
      </div>
    </section>

    <!-- FEATURES -->
    <section id="features" style="padding: 6rem 0; border-top: 1px solid rgba(37,99,235,0.1);">
      <div class="container">
        <div style="text-align: center; margin-bottom: 3rem;">
          <h2 style="font-size: 2rem; font-weight: 700; margin-bottom: 0.75rem;">Todo lo que necesitas</h2>
          <p style="color: var(--muted);">Un SaaS completo de facturación electrónica sin instalaciones complicadas.</p>
        </div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.25rem;">
          <div v-for="feat in features" :key="feat.title" class="card"
            style="transition: border-color 0.2s, transform 0.2s;" 
            onmouseover="this.style.borderColor='rgba(37,99,235,0.4)'; this.style.transform='translateY(-3px)'"
            onmouseout="this.style.borderColor='rgba(37,99,235,0.15)'; this.style.transform='translateY(0)'">
            <div style="font-size: 2rem; margin-bottom: 0.875rem;">{{ feat.icon }}</div>
            <h3 style="font-size: 1rem; font-weight: 700; margin-bottom: 0.5rem;">{{ feat.title }}</h3>
            <p style="font-size: 0.875rem; color: var(--muted); line-height: 1.6;">{{ feat.desc }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- COMPLIANCE BANNER -->
    <section style="padding: 4rem 0; background: linear-gradient(135deg, rgba(37,99,235,0.08), rgba(6,182,212,0.05)); border-top: 1px solid rgba(37,99,235,0.1); border-bottom: 1px solid rgba(37,99,235,0.1);">
      <div class="container" style="text-align: center;">
        <div style="display: inline-flex; align-items: center; gap: 0.75rem; background: rgba(16,185,129,0.1); border: 1px solid rgba(16,185,129,0.3); border-radius: 12px; padding: 0.875rem 1.5rem; margin-bottom: 1.5rem;">
          <span style="font-size: 1.25rem;">✅</span>
          <span style="font-weight: 600; color: #34D399;">100% Compatible con Hacienda CR</span>
        </div>
        <h2 style="font-size: 1.75rem; font-weight: 700; margin-bottom: 1rem;">Cumplimiento Normativo Garantizado</h2>
        <div style="display: flex; gap: 2rem; justify-content: center; flex-wrap: wrap; margin-top: 1.5rem;">
          <div v-for="c in compliance" :key="c" style="display: flex; align-items: center; gap: 0.5rem; font-size: 0.9rem; color: var(--muted);">
            <span style="color: #34D399;">✓</span> {{ c }}
          </div>
        </div>
      </div>
    </section>

    <!-- PRICING -->
    <section id="pricing" style="padding: 6rem 0;">
      <div class="container">
        <div style="text-align: center; margin-bottom: 3rem;">
          <h2 style="font-size: 2rem; font-weight: 700; margin-bottom: 0.75rem;">Planes simples y transparentes</h2>
          <p style="color: var(--muted);">Sin contratos. Cancela cuando quieras.</p>
        </div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.5rem; max-width: 900px; margin: 0 auto;">
          <div v-for="plan in plans" :key="plan.name" class="card"
            :style="plan.featured ? 'border-color: rgba(37,99,235,0.5); background: rgba(37,99,235,0.05);' : ''">
            <div v-if="plan.featured" style="display: inline-block; background: #2563EB; color: white; font-size: 0.7rem; font-weight: 700; padding: 0.2rem 0.625rem; border-radius: 4px; margin-bottom: 0.75rem; text-transform: uppercase; letter-spacing: 0.5px;">POPULAR</div>
            <h3 style="font-size: 1.25rem; font-weight: 700;">{{ plan.name }}</h3>
            <div style="margin: 1rem 0;">
              <span style="font-size: 2.5rem; font-weight: 800;">{{ plan.price }}</span>
              <span style="color: var(--muted); font-size: 0.875rem;">/mes</span>
            </div>
            <p style="font-size: 0.875rem; color: var(--muted); margin-bottom: 1.5rem;">{{ plan.desc }}</p>
            <ul style="list-style: none; display: flex; flex-direction: column; gap: 0.625rem; margin-bottom: 1.75rem;">
              <li v-for="f in plan.features" :key="f" style="display: flex; align-items: center; gap: 0.5rem; font-size: 0.875rem;">
                <span style="color: #10B981;">✓</span> {{ f }}
              </li>
            </ul>
            <a href="http://localhost:3000/auth/register" class="btn" :class="plan.featured ? 'btn-primary' : 'btn-ghost'" style="display: block; text-align: center;">
              {{ plan.cta }}
            </a>
          </div>
        </div>
      </div>
    </section>

    <!-- FOOTER -->
    <footer style="border-top: 1px solid rgba(37,99,235,0.1); padding: 2.5rem 0;">
      <div class="container" style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
        <div style="display: flex; align-items: center; gap: 0.625rem;">
          <div style="width: 28px; height: 28px; background: #2563EB; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-size: 0.875rem; color: white; font-weight: 800;">₡</div>
          <span style="font-weight: 700;">Factura CR</span>
          <span style="color: var(--muted); font-size: 0.8rem; margin-left: 4px;">© 2026 Zona Sur Tech</span>
        </div>
        <p style="font-size: 0.8rem; color: var(--muted);">Comprobantes Electrónicos v4.4 · Ministerio de Hacienda Costa Rica</p>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
const stats = [
  { value: "50",    label: "Dígitos en clave única" },
  { value: "v4.4",  label: "Estándar Hacienda" },
  { value: "XAdES", label: "Firma digital BCCR" },
  { value: "4",     label: "Tipos de comprobante" },
]

const features = [
  { icon: "📄", title: "XML v4.4 Automático",      desc: "Genera XML 100% compatible con Hacienda CR: FacturaElectronica, TiqueteElectronico, NotaCredito, NotaDebito." },
  { icon: "🔐", title: "Firma Digital XAdES",       desc: "Firma tu comprobante con certificado .p12 del BCCR. Compatible con el sistema de validación de Hacienda." },
  { icon: "🚀", title: "Envío en Tiempo Real",       desc: "Pipeline automatizado: generar → firmar → convertir a Base64 → enviar a API de Hacienda → consultar estado." },
  { icon: "📊", title: "Dashboard Financiero",       desc: "Panel estilo Stripe con métricas: ingresos del mes, facturas emitidas, IVA acumulado, clientes activos." },
  { icon: "🏷",  title: "Catálogo CABYS",            desc: "Busca y asigna el código CABYS correcto a cada producto o servicio según el catálogo oficial de Hacienda." },
  { icon: "📑", title: "PDF con QR",                 desc: "Genera el PDF de cada factura con logo, desglose de impuestos y QR de verificación en el portal de Hacienda." },
  { icon: "🏢", title: "Multi-empresa",              desc: "Gestiona múltiples empresas desde una sola cuenta. Row Level Security garantiza separación total de datos." },
  { icon: "⚡", title: "Workers asíncronos",         desc: "Procesamiento en background con Celery + Redis para no bloquear la interfaz durante el envío a Hacienda." },
]

const compliance = [
  "Clave numérica 50 dígitos",
  "XML Hacienda v4.4",
  "Firma XAdES-BES",
  "OAuth2 IDP Hacienda",
  "Sandbox / Producción",
  "CABYS integrado",
  "IVA Costa Rica (13%, 8%, 4%, 2%, 1%, 0%)",
]

const plans = [
  {
    name: "Starter",
    price: "₡0",
    desc: "Para empezar a probar",
    featured: false,
    cta: "Empezar gratis",
    features: [
      "50 facturas/mes",
      "Dashboard básico",
      "Sandbox Hacienda",
      "Soporte por email",
    ],
  },
  {
    name: "Pro",
    price: "₡15.000",
    desc: "Para empresas en crecimiento",
    featured: true,
    cta: "Comenzar ahora →",
    features: [
      "500 facturas/mes",
      "Dashboard completo",
      "Producción Hacienda",
      "Firma digital BCCR",
      "PDF con QR",
      "Soporte prioritario",
    ],
  },
  {
    name: "Enterprise",
    price: "₡45.000",
    desc: "Para grandes volúmenes",
    featured: false,
    cta: "Contactar ventas",
    features: [
      "Facturas ilimitadas",
      "Multi-empresa",
      "API acceso completo",
      "SLA 99.9%",
      "Soporte dedicado",
    ],
  },
]

useHead({ title: "Factura CR — Facturación Electrónica para Costa Rica" })
</script>
