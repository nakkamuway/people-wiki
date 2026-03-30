import { useDb } from '~/server/db'
import { familyMembers, people } from '~/server/db/schema'
import { eq, and } from 'drizzle-orm'

const reverseRelationship: Record<string, string> = {
  '配偶者': '配偶者',
  '父親': '子供',
  '母親': '子供',
  '子供': '親',
  '兄弟姉妹': '兄弟姉妹',
  'その他': 'その他',
}

export default defineEventHandler(async (event) => {
  requireAuth(event)
  const db = useDb()
  const body = await readBody(event)

  const [created] = await db.insert(familyMembers).values({
    personId: body.personId,
    name: body.name,
    relationship: body.relationship,
    birthday: body.birthday || null,
    linkedPersonId: body.linkedPersonId || null,
  }).returning()

  await db.update(people).set({ updatedAt: new Date() }).where(eq(people.id, body.personId))

  // 既存人物とリンクされている場合、相手側にも逆の関係を自動追加
  if (body.linkedPersonId) {
    const existing = await db.select().from(familyMembers).where(
      and(
        eq(familyMembers.personId, body.linkedPersonId),
        eq(familyMembers.linkedPersonId, body.personId),
      )
    )
    if (existing.length === 0) {
      const sourcePerson = await db.select().from(people).where(eq(people.id, body.personId))
      const reverse = reverseRelationship[body.relationship] || 'その他'
      await db.insert(familyMembers).values({
        personId: body.linkedPersonId,
        name: sourcePerson[0]?.name || body.name,
        relationship: reverse,
        birthday: sourcePerson[0]?.birthday || null,
        linkedPersonId: body.personId,
      })
      await db.update(people).set({ updatedAt: new Date() }).where(eq(people.id, body.linkedPersonId))
    }
  }

  return created
})
