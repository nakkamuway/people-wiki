import { useDb } from '~/server/db'
import { familyMembers } from '~/server/db/schema'
import { eq, and } from 'drizzle-orm'

export default defineEventHandler(async (event) => {
  requireAuth(event)
  const db = useDb()
  const id = Number(getRouterParam(event, 'id'))

  // 削除前にリンク情報を取得
  const [target] = await db.select().from(familyMembers).where(eq(familyMembers.id, id))

  await db.delete(familyMembers).where(eq(familyMembers.id, id))

  // 相手側の逆リンクも削除
  if (target?.linkedPersonId) {
    await db.delete(familyMembers).where(
      and(
        eq(familyMembers.personId, target.linkedPersonId),
        eq(familyMembers.linkedPersonId, target.personId),
      )
    )
  }

  return { ok: true }
})
