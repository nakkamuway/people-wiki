export function useAuth() {
  const authenticated = useState<boolean>('auth', () => false)
  const checking = useState<boolean>('auth-checking', () => true)

  async function check() {
    try {
      const { authenticated: isAuth } = await $fetch<{ authenticated: boolean }>('/api/auth/check')
      authenticated.value = isAuth
    } catch {
      authenticated.value = false
    } finally {
      checking.value = false
    }
  }

  async function login(password: string) {
    await $fetch('/api/auth/login', { method: 'POST', body: { password } })
    authenticated.value = true
  }

  async function logout() {
    await $fetch('/api/auth/logout', { method: 'POST' })
    authenticated.value = false
    navigateTo('/')
  }

  return { authenticated, checking, check, login, logout }
}
