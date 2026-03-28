import { useDb } from '~/server/db'
import { events, people } from '~/server/db/schema'
import { eq } from 'drizzle-orm'

export default defineEventHandler(async (event) => {
  requireAuth(event)
  const db = useDb()
  const body = await readBody(event)

  const [created] = await db.insert(events).values({
    personId: body.personId,
    eventDate: body.eventDate,
    content: body.content,
    imageUrl: body.imageUrl || null,
  }).returning()

  // Update person's updatedAt
  await db.update(people).set({ updatedAt: new Date() }).where(eq(people.id, body.personId))

  return created
})
