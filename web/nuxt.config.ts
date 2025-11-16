import tailwindcss from "@tailwindcss/vite";

// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },
  css: ['~/assets/css/main.css'],
  nitro: {
    preset: 'cloudflare_module',
  },
  vite: {
    plugins: [
      tailwindcss(),
    ],
  },
  modules: ['shadcn-nuxt', '@nuxt/icon'],
  shadcn: {
    prefix: '',
    /**
     * Directory that the component lives in.
     * @default "./components/ui"
     */
    componentDir: './components/ui'
  },
  runtimeConfig: {
    // Private keys (only available on server-side)
    // Public keys (exposed to client-side)
    public: {
      apiBaseUrl: process.env.API_BASE_URL || 'http://localhost:8000',
    },
  },
})