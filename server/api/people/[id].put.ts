import { useDb } from '~/server/db'
import { people } from '~/server/db/schema'
import { eq } from 'drizzle-orm'

export default defineEventHandler(async (event) => {
  requireAuth(event)
  const db = useDb()
  const id = Number(getRouterParam(event, 'id'))
  const body = await readBody(event)

  const [updated] = await db.update(people).set({
    name: body.name,
    organization: body.organization || null,
    metAt: body.metAt || null,
    birthday: body.birthday || null,
    notes: body.notes || null,
    twitter: body.twitter || null,
    instagram: body.instagram || null,
    facebook: body.facebook || null,
    linkedin: body.linkedin || null,
    maritalStatus: body.maritalStatus || null,
    hasChildren: body.hasChildren || null,
    hasPets: body.hasPets || null,
    imageUrl: body.imageUrl || null,
    updatedAt: new Date(),
  }).where(eq(people.id, id)).returning()

  if (!updated) throw createError({ statusCode: 404, message: '人物が見つかりません' })
  return updated
})
