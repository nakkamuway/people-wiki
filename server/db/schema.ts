import { pgTable, serial, text, timestamp } from 'drizzle-orm/pg-core'

export const people = pgTable('people', {
  id: serial('id').primaryKey(),
  name: text('name').notNull(),
  organization: text('organization'),
  metAt: text('met_at'),
  birthday: text('birthday'),
  notes: text('notes'),
  twitter: text('twitter'),
  instagram: text('instagram'),
  facebook: text('facebook'),
  linkedin: text('linkedin'),
  maritalStatus: text('marital_status'),
  hasChildren: text('has_children'),
  hasPets: text('has_pets'),
  imageUrl: text('image_url'),
  createdAt: timestamp('created_at').defaultNow().notNull(),
  updatedAt: timestamp('updated_at').defaultNow().notNull(),
})

export const events = pgTable('events', {
  id: serial('id').primaryKey(),
  personId: serial('person_id').references(() => people.id, { onDelete: 'cascade' }).notNull(),
  eventDate: text('event_date').notNull(),
  content: text('content').notNull(),
  imageUrl: text('image_url'),
  createdAt: timestamp('created_at').defaultNow().notNull(),
})

export const familyMembers = pgTable('family_members', {
  id: serial('id').primaryKey(),
  personId: serial('person_id').references(() => people.id, { onDelete: 'cascade' }).notNull(),
  name: text('name').notNull(),
  relationship: text('relationship').notNull(),
  birthday: text('birthday'),
  linkedPersonId: serial('linked_person_id'),
  createdAt: timestamp('created_at').defaultNow().notNull(),
})
