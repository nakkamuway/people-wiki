import { useDb } from '~/server/db'
import { people } from '~/server/db/schema'

export default defineEventHandler(async (event) => {
  requireAuth(event)
  const db = useDb()
  const body = await readBody(event)

  const [person] = await db.insert(people).values({
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
  }).returning()

  return person
})
