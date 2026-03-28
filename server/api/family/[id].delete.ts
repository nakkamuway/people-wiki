import { useDb } from '~/server/db'
import { familyMembers } from '~/server/db/schema'
import { eq } from 'drizzle-orm'

export default defineEventHandler(async (event) => {
  requireAuth(event)
  const db = useDb()
  const id = Number(getRouterParam(event, 'id'))

  await db.delete(familyMembers).where(eq(familyMembers.id, id))
  return { ok: true }
})
