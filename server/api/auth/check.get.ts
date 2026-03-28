export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  const session = getCookie(event, 'people-wiki-session')
  return { authenticated: session === config.session.secret }
})
