import { useDb } from '~/server/db'
import { events } from '~/server/db/schema'
import { eq } from 'drizzle-orm'

export default defineEventHandler(async (event) => {
  requireAuth(event)
  const db = useDb()
  const id = Number(getRouterParam(event, 'id'))

  await db.delete(events).where(eq(events.id, id))
  return { ok: true }
})
