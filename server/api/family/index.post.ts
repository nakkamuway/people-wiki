import { useDb } from '~/server/db'
import { familyMembers, people } from '~/server/db/schema'
import { eq } from 'drizzle-orm'

export default defineEventHandler(async (event) => {
  requireAuth(event)
  const db = useDb()
  const body = await readBody(event)

  const [created] = await db.insert(familyMembers).values({
    personId: body.personId,
    name: body.name,
    relationship: body.relationship,
    birthday: body.birthday || null,
  }).returning()

  await db.update(people).set({ updatedAt: new Date() }).where(eq(people.id, body.personId))

  return created
})
