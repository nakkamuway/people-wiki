import { useDb } from '~/server/db'
import { people } from '~/server/db/schema'
import { desc, ilike, or } from 'drizzle-orm'

export default defineEventHandler(async (event) => {
  requireAuth(event)
  const db = useDb()
  const query = getQuery(event)
  const search = (query.q as string) || ''
  const sort = (query.sort as string) || 'updated'

  let q = db.select().from(people)

  if (search) {
    q = q.where(
      or(
        ilike(people.name, `%${search}%`),
        ilike(people.organization, `%${search}%`),
        ilike(people.notes, `%${search}%`),
      ),
    ) as typeof q
  }

  if (sort === 'birthday') {
    // Sort in app layer for birthday proximity logic
    const rows = await q
    return rows.sort((a, b) => {
      const da = daysUntilBirthday(a.birthday)
      const db_ = daysUntilBirthday(b.birthday)
      return da - db_
    })
  }

  return await q.orderBy(desc(people.updatedAt))
})

function daysUntilBirthday(birthday: string | null): number {
  if (!birthday) return 9999
  const today = new Date()
  const [, m, d] = birthday.split('-').map(Number)
  if (!m || !d) return 9999
  let next = new Date(today.getFullYear(), m - 1, d)
  if (next < today) next = new Date(today.getFullYear() + 1, m - 1, d)
  return Math.ceil((next.getTime() - today.getTime()) / (1000 * 60 * 60 * 24))
}
