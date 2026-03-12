// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  devtools: { enabled: true },

  modules: ['@nuxt/ui', '@nuxtjs/tailwindcss'],

  app: {
    head: {
      title: 'Factura CR — Facturación Electrónica para Costa Rica',
      meta: [
        { name: 'description', content: 'SaaS de facturación electrónica para Costa Rica. Compatible con Hacienda v4.4. Multi-empresa, firma digital BCCR, envío automático.' },
        { name: 'theme-color', content: '#0D1B2E' },
        { property: 'og:title', content: 'Factura CR — Facturación Electrónica' },
        { property: 'og:description', content: 'La plataforma SaaS más moderna para emisión de comprobantes electrónicos en Costa Rica.' },
      ],
      link: [
        { rel: 'preconnect', href: 'https://fonts.googleapis.com' },
        { rel: 'stylesheet', href: 'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap' },
      ],
    },
  },

  colorMode: { classSuffix: '' },

  typescript: { strict: true },

  css: ['~/assets/css/landing.css'],
})
