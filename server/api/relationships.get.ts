import { useDb } from '~/server/db'
import { people, familyMembers } from '~/server/db/schema'

export default defineEventHandler(async (event) => {
  requireAuth(event)
  const db = useDb()

  const allPeople = await db.select({
    id: people.id,
    name: people.name,
    organization: people.organization,
  }).from(people)

  const allFamily = await db.select().from(familyMembers)

  return { people: allPeople, relationships: allFamily }
})
