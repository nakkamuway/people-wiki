export default defineEventHandler(async (event) => {
  const { password } = await readBody(event)
  const config = useRuntimeConfig()

  if (password !== config.authPassword) {
    throw createError({ statusCode: 401, message: 'パスワードが正しくありません' })
  }

  // Set a signed cookie as session
  setCookie(event, 'people-wiki-session', config.session.secret, {
    httpOnly: true,
    secure: true,
    sameSite: 'lax',
    maxAge: 60 * 60 * 24 * 30, // 30 days
    path: '/',
  })

  return { ok: true }
})
