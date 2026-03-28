export default defineEventHandler(async (event) => {
  deleteCookie(event, 'people-wiki-session', { path: '/' })
  return { ok: true }
})
