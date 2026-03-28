import { useDb } from '~/server/db'
import { people, events, familyMembers } from '~/server/db/schema'
import { eq, desc } from 'drizzle-orm'

export default defineEventHandler(async (event) => {
  requireAuth(event)
  const db = useDb()
  const id = Number(getRouterParam(event, 'id'))

  const [person] = await db.select().from(people).where(eq(people.id, id))
  if (!person) throw createError({ statusCode: 404, message: '人物が見つかりません' })

  const personEvents = await db.select().from(events)
    .where(eq(events.personId, id))
    .orderBy(desc(events.eventDate))

  const family = await db.select().from(familyMembers)
    .where(eq(familyMembers.personId, id))

  return { ...person, events: personEvents, family }
})
