import tailwindcss from '@tailwindcss/vite'

export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },

  modules: ['@nuxtjs/google-fonts'],

  css: ['~/assets/css/main.css'],

  vite: {
    plugins: [tailwindcss()],
  },

  googleFonts: {
    families: {
      'Playfair Display': [400, 700],
      'Inter': [300, 400, 500, 600],
    },
    display: 'swap',
  },

  runtimeConfig: {
    databaseUrl: '',
    authPassword: '',
    session: {
      secret: '',
    },
  },
})
