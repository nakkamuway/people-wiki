import type { H3Event } from 'h3'

export function requireAuth(event: H3Event) {
  const config = useRuntimeConfig()
  const session = getCookie(event, 'people-wiki-session')
  if (session !== config.session.secret) {
    throw createError({ statusCode: 401, message: '認証が必要です' })
  }
}
