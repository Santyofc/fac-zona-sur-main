// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  devtools: { enabled: true },

  modules: [
    "@nuxt/ui",
    "@nuxtjs/supabase",
    "@nuxtjs/tailwindcss",
  ],

  supabase: {
    redirect: false,
  },

  ui: {
    global: true,
  },

  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || "http://localhost:8000",
      supabaseUrl: process.env.NUXT_PUBLIC_SUPABASE_URL || "",
      supabaseKey: process.env.NUXT_PUBLIC_SUPABASE_KEY || "",
      appName: "Factura CR",
    },
  },

  app: {
    head: {
      title: "Factura CR — Facturación Electrónica",
      meta: [
        { charset: "utf-8" },
        { name: "viewport", content: "width=device-width, initial-scale=1" },
        {
          name: "description",
          content: "Plataforma SaaS de facturación electrónica para Costa Rica. Compatible con Ministerio de Hacienda.",
        },
      ],
      link: [
        { rel: "icon", type: "image/svg+xml", href: "/favicon.svg" },
        {
          rel: "stylesheet",
          href: "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap",
        },
      ],
    },
  },

  tailwindcss: {
    cssPath: "~/assets/css/tailwind.css",
    configPath: "tailwind.config.ts",
  },

  typescript: {
    strict: true,
    shim: false,
  },

  compatibilityDate: "2024-02-08",
})
