import { useDb } from '~/server/db'
import { people } from '~/server/db/schema'
import { eq } from 'drizzle-orm'

export default defineEventHandler(async (event) => {
  requireAuth(event)
  const db = useDb()
  const id = Number(getRouterParam(event, 'id'))

  await db.delete(people).where(eq(people.id, id))
  return { ok: true }
})
