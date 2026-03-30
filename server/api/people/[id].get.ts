import { useDb } from '~/server/db'
import { people, events, familyMembers } from '~/server/db/schema'
import { eq, desc, sql } from 'drizzle-orm'

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

  // リンク先人物のイベント数を取得（関係マップの表示サイズ用）
  const linkedIds = family.filter(f => f.linkedPersonId).map(f => f.linkedPersonId!)
  let eventCounts: Record<number, number> = {}
  if (linkedIds.length > 0) {
    const counts = await db.select({
      personId: events.personId,
      count: sql<number>`count(*)::int`,
    }).from(events)
      .where(sql`${events.personId} IN (${sql.join(linkedIds.map(id => sql`${id}`), sql`, `)})`)
      .groupBy(events.personId)
    for (const c of counts) {
      eventCounts[c.personId] = c.count
    }
  }

  const familyWithCounts = family.map(f => ({
    ...f,
    eventCount: f.linkedPersonId ? (eventCounts[f.linkedPersonId] || 0) : 0,
  }))

  return { ...person, events: personEvents, family: familyWithCounts }
})
