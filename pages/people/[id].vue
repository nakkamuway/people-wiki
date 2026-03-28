<template>
  <NuxtLayout name="default">
    <div v-if="!person" class="text-center py-20">
      <p class="text-text-muted">Loading...</p>
    </div>

    <div v-else class="space-y-8">
      <!-- Back -->
      <NuxtLink to="/" class="inline-flex items-center gap-2 text-sm text-text-muted hover:text-text-primary transition-colors">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>
        Back
      </NuxtLink>

      <!-- Person Header -->
      <div class="border-b border-border pb-8">
        <div class="flex items-start justify-between">
          <div class="flex items-center gap-5">
            <div class="w-20 h-20 rounded-full bg-bg-card border border-border flex items-center justify-center text-text-muted font-serif text-3xl overflow-hidden">
              <img v-if="person.imageUrl" :src="person.imageUrl" :alt="person.name" class="w-full h-full object-cover" />
              <span v-else>{{ person.name[0] }}</span>
            </div>
            <div>
              <h1 class="font-serif text-4xl text-text-primary">{{ person.name }}</h1>
              <p v-if="person.organization" class="text-text-secondary mt-1">{{ person.organization }}</p>
            </div>
          </div>
          <div class="flex gap-2">
            <button
              @click="editing = !editing"
              class="text-sm border border-border text-text-secondary rounded-lg px-4 py-2 hover:bg-bg-hover transition-colors"
            >
              {{ editing ? 'Cancel' : 'Edit' }}
            </button>
            <button
              @click="deletePerson"
              class="text-sm border border-border text-danger rounded-lg px-4 py-2 hover:bg-bg-hover transition-colors"
            >
              Delete
            </button>
          </div>
        </div>
      </div>

      <!-- Edit Form -->
      <div v-if="editing" class="bg-bg-secondary border border-border rounded-xl p-6 space-y-4">
        <h2 class="font-serif text-xl text-text-primary">Edit Person</h2>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm text-text-secondary mb-1">Name *</label>
            <input v-model="editForm.name" required class="w-full bg-bg-card border border-border rounded-lg px-4 py-2.5 text-text-primary focus:outline-none focus:border-accent" />
          </div>
          <div>
            <label class="block text-sm text-text-secondary mb-1">Organization</label>
            <input v-model="editForm.organization" class="w-full bg-bg-card border border-border rounded-lg px-4 py-2.5 text-text-primary focus:outline-none focus:border-accent" />
          </div>
          <div>
            <label class="block text-sm text-text-secondary mb-1">Birthday</label>
            <input v-model="editForm.birthday" type="date" class="w-full bg-bg-card border border-border rounded-lg px-4 py-2.5 text-text-primary focus:outline-none focus:border-accent" />
          </div>
          <div>
            <label class="block text-sm text-text-secondary mb-1">Met at</label>
            <input v-model="editForm.metAt" class="w-full bg-bg-card border border-border rounded-lg px-4 py-2.5 text-text-primary focus:outline-none focus:border-accent" />
          </div>
          <div>
            <label class="block text-sm text-text-secondary mb-1">Marital Status</label>
            <select v-model="editForm.maritalStatus" class="w-full bg-bg-card border border-border rounded-lg px-4 py-2.5 text-text-primary focus:outline-none focus:border-accent">
              <option value="">-</option>
              <option value="既婚">既婚</option>
              <option value="未婚">未婚</option>
            </select>
          </div>
          <div>
            <label class="block text-sm text-text-secondary mb-1">Children</label>
            <select v-model="editForm.hasChildren" class="w-full bg-bg-card border border-border rounded-lg px-4 py-2.5 text-text-primary focus:outline-none focus:border-accent">
              <option value="">-</option>
              <option value="あり">あり</option>
              <option value="なし">なし</option>
            </select>
          </div>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm text-text-secondary mb-1">Twitter</label>
            <input v-model="editForm.twitter" class="w-full bg-bg-card border border-border rounded-lg px-4 py-2.5 text-text-primary focus:outline-none focus:border-accent" />
          </div>
          <div>
            <label class="block text-sm text-text-secondary mb-1">Instagram</label>
            <input v-model="editForm.instagram" class="w-full bg-bg-card border border-border rounded-lg px-4 py-2.5 text-text-primary focus:outline-none focus:border-accent" />
          </div>
          <div>
            <label class="block text-sm text-text-secondary mb-1">Facebook</label>
            <input v-model="editForm.facebook" class="w-full bg-bg-card border border-border rounded-lg px-4 py-2.5 text-text-primary focus:outline-none focus:border-accent" />
          </div>
          <div>
            <label class="block text-sm text-text-secondary mb-1">LinkedIn</label>
            <input v-model="editForm.linkedin" class="w-full bg-bg-card border border-border rounded-lg px-4 py-2.5 text-text-primary focus:outline-none focus:border-accent" />
          </div>
        </div>
        <div>
          <label class="block text-sm text-text-secondary mb-1">Notes</label>
          <textarea v-model="editForm.notes" rows="3" class="w-full bg-bg-card border border-border rounded-lg px-4 py-2.5 text-text-primary focus:outline-none focus:border-accent resize-none" />
        </div>
        <div class="flex gap-3 pt-2">
          <button @click="editing = false" class="border border-border text-text-secondary rounded-lg px-6 py-2.5 hover:bg-bg-hover transition-colors">Cancel</button>
          <button @click="savePerson" class="bg-accent hover:bg-accent-hover text-bg-primary font-medium rounded-lg px-6 py-2.5 transition-colors">Save</button>
        </div>
      </div>

      <!-- Info Cards -->
      <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <!-- Details -->
        <div class="bg-bg-secondary border border-border rounded-xl p-6 space-y-4">
          <h2 class="font-serif text-lg text-text-primary border-b border-border pb-3">Details</h2>
          <dl class="space-y-3 text-sm">
            <div v-if="person.birthday" class="flex justify-between">
              <dt class="text-text-muted">Birthday</dt>
              <dd class="text-text-primary">{{ formatBirthday(person.birthday) }}</dd>
            </div>
            <div v-if="person.metAt" class="flex justify-between">
              <dt class="text-text-muted">Met at</dt>
              <dd class="text-text-primary">{{ person.metAt }}</dd>
            </div>
            <div v-if="person.maritalStatus" class="flex justify-between">
              <dt class="text-text-muted">Marital</dt>
              <dd class="text-text-primary">{{ person.maritalStatus }}</dd>
            </div>
            <div v-if="person.hasChildren" class="flex justify-between">
              <dt class="text-text-muted">Children</dt>
              <dd class="text-text-primary">{{ person.hasChildren }}</dd>
            </div>
            <div v-if="person.hasPets" class="flex justify-between">
              <dt class="text-text-muted">Pets</dt>
              <dd class="text-text-primary">{{ person.hasPets }}</dd>
            </div>
          </dl>
        </div>

        <!-- SNS -->
        <div class="bg-bg-secondary border border-border rounded-xl p-6 space-y-4">
          <h2 class="font-serif text-lg text-text-primary border-b border-border pb-3">Links</h2>
          <div class="space-y-3 text-sm">
            <a v-if="person.twitter" :href="person.twitter" target="_blank" class="flex items-center gap-2 text-text-secondary hover:text-accent transition-colors">
              <span class="text-text-muted">Twitter</span>
              <span class="truncate">{{ person.twitter }}</span>
            </a>
            <a v-if="person.instagram" :href="person.instagram" target="_blank" class="flex items-center gap-2 text-text-secondary hover:text-accent transition-colors">
              <span class="text-text-muted">Instagram</span>
              <span class="truncate">{{ person.instagram }}</span>
            </a>
            <a v-if="person.facebook" :href="person.facebook" target="_blank" class="flex items-center gap-2 text-text-secondary hover:text-accent transition-colors">
              <span class="text-text-muted">Facebook</span>
              <span class="truncate">{{ person.facebook }}</span>
            </a>
            <a v-if="person.linkedin" :href="person.linkedin" target="_blank" class="flex items-center gap-2 text-text-secondary hover:text-accent transition-colors">
              <span class="text-text-muted">LinkedIn</span>
              <span class="truncate">{{ person.linkedin }}</span>
            </a>
            <p v-if="!person.twitter && !person.instagram && !person.facebook && !person.linkedin" class="text-text-muted">
              No links added
            </p>
          </div>
        </div>

        <!-- Notes -->
        <div v-if="person.notes" class="bg-bg-secondary border border-border rounded-xl p-6 md:col-span-2">
          <h2 class="font-serif text-lg text-text-primary border-b border-border pb-3 mb-4">Notes</h2>
          <p class="text-text-secondary text-sm whitespace-pre-wrap">{{ person.notes }}</p>
        </div>
      </div>

      <!-- Family -->
      <div class="space-y-4">
        <div class="flex items-center justify-between">
          <h2 class="font-serif text-2xl text-text-primary">Family</h2>
          <button @click="showFamilyModal = true" class="text-sm text-accent hover:text-accent-hover transition-colors">+ Add</button>
        </div>
        <div v-if="person.family?.length" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          <div v-for="fm in person.family" :key="fm.id" class="bg-bg-card border border-border rounded-lg p-4 flex items-center justify-between">
            <div>
              <span class="text-xs text-accent uppercase tracking-wider">{{ fm.relationship }}</span>
              <p class="text-text-primary text-sm mt-0.5">{{ fm.name }}</p>
              <p v-if="fm.birthday" class="text-xs text-text-muted mt-0.5">{{ formatBirthday(fm.birthday) }}</p>
            </div>
            <button @click="deleteFamily(fm.id)" class="text-text-muted hover:text-danger transition-colors text-xs">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
            </button>
          </div>
        </div>
        <p v-else class="text-text-muted text-sm">No family members added</p>
      </div>

      <!-- Timeline -->
      <div class="space-y-4">
        <div class="flex items-center justify-between">
          <h2 class="font-serif text-2xl text-text-primary">Timeline</h2>
          <button @click="showEventModal = true" class="text-sm text-accent hover:text-accent-hover transition-colors">+ Add Event</button>
        </div>
        <div v-if="person.events?.length" class="space-y-3">
          <div v-for="ev in person.events" :key="ev.id" class="bg-bg-card border border-border rounded-lg p-4 group">
            <div class="flex items-start justify-between">
              <div>
                <p class="text-xs text-text-muted">{{ formatEventDate(ev.eventDate) }}</p>
                <p class="text-text-primary text-sm mt-1 whitespace-pre-wrap">{{ ev.content }}</p>
                <img v-if="ev.imageUrl" :src="ev.imageUrl" class="mt-3 rounded-lg max-w-xs" />
              </div>
              <button @click="deleteEvent(ev.id)" class="text-text-muted hover:text-danger transition-colors opacity-0 group-hover:opacity-100">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
              </button>
            </div>
          </div>
        </div>
        <p v-else class="text-text-muted text-sm">No events yet</p>
      </div>
    </div>

    <!-- Add Family Modal -->
    <Teleport to="body">
      <div v-if="showFamilyModal" class="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4" @click.self="showFamilyModal = false">
        <div class="bg-bg-secondary border border-border rounded-xl w-full max-w-md p-6">
          <h2 class="font-serif text-xl text-text-primary mb-4">Add Family Member</h2>
          <form @submit.prevent="addFamily" class="space-y-4">
            <div>
              <label class="block text-sm text-text-secondary mb-1">Name *</label>
              <input v-model="newFamily.name" required class="w-full bg-bg-card border border-border rounded-lg px-4 py-2.5 text-text-primary focus:outline-none focus:border-accent" />
            </div>
            <div>
              <label class="block text-sm text-text-secondary mb-1">Relationship *</label>
              <select v-model="newFamily.relationship" required class="w-full bg-bg-card border border-border rounded-lg px-4 py-2.5 text-text-primary focus:outline-none focus:border-accent">
                <option value="">Select...</option>
                <option v-for="r in ['配偶者','子供','父親','母親','兄弟姉妹','その他']" :key="r" :value="r">{{ r }}</option>
              </select>
            </div>
            <div>
              <label class="block text-sm text-text-secondary mb-1">Birthday</label>
              <input v-model="newFamily.birthday" type="date" class="w-full bg-bg-card border border-border rounded-lg px-4 py-2.5 text-text-primary focus:outline-none focus:border-accent" />
            </div>
            <div class="flex gap-3 pt-2">
              <button type="button" @click="showFamilyModal = false" class="flex-1 border border-border text-text-secondary rounded-lg py-2.5 hover:bg-bg-hover transition-colors">Cancel</button>
              <button type="submit" class="flex-1 bg-accent hover:bg-accent-hover text-bg-primary font-medium rounded-lg py-2.5 transition-colors">Add</button>
            </div>
          </form>
        </div>
      </div>
    </Teleport>

    <!-- Add Event Modal -->
    <Teleport to="body">
      <div v-if="showEventModal" class="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4" @click.self="showEventModal = false">
        <div class="bg-bg-secondary border border-border rounded-xl w-full max-w-md p-6">
          <h2 class="font-serif text-xl text-text-primary mb-4">Add Event</h2>
          <form @submit.prevent="addEvent" class="space-y-4">
            <div>
              <label class="block text-sm text-text-secondary mb-1">Date *</label>
              <input v-model="newEvent.eventDate" type="date" required class="w-full bg-bg-card border border-border rounded-lg px-4 py-2.5 text-text-primary focus:outline-none focus:border-accent" />
            </div>
            <div>
              <label class="block text-sm text-text-secondary mb-1">Content *</label>
              <textarea v-model="newEvent.content" required rows="4" class="w-full bg-bg-card border border-border rounded-lg px-4 py-2.5 text-text-primary focus:outline-none focus:border-accent resize-none" />
            </div>
            <div class="flex gap-3 pt-2">
              <button type="button" @click="showEventModal = false" class="flex-1 border border-border text-text-secondary rounded-lg py-2.5 hover:bg-bg-hover transition-colors">Cancel</button>
              <button type="submit" class="flex-1 bg-accent hover:bg-accent-hover text-bg-primary font-medium rounded-lg py-2.5 transition-colors">Add</button>
            </div>
          </form>
        </div>
      </div>
    </Teleport>
  </NuxtLayout>
</template>

<script setup lang="ts">
const route = useRoute()
const person = ref<any>(null)
const editing = ref(false)
const editForm = ref<any>({})
const showFamilyModal = ref(false)
const showEventModal = ref(false)
const newFamily = ref({ name: '', relationship: '', birthday: '' })
const newEvent = ref({ eventDate: '', content: '' })

async function fetchPerson() {
  person.value = await $fetch(`/api/people/${route.params.id}`)
  editForm.value = { ...person.value }
}

async function savePerson() {
  await $fetch(`/api/people/${route.params.id}`, { method: 'PUT', body: editForm.value })
  editing.value = false
  await fetchPerson()
}

async function deletePerson() {
  if (!confirm('この人物を削除しますか？')) return
  await $fetch(`/api/people/${route.params.id}`, { method: 'DELETE' })
  navigateTo('/')
}

async function addFamily() {
  await $fetch('/api/family', {
    method: 'POST',
    body: { ...newFamily.value, personId: Number(route.params.id) },
  })
  showFamilyModal.value = false
  newFamily.value = { name: '', relationship: '', birthday: '' }
  await fetchPerson()
}

async function deleteFamily(id: number) {
  if (!confirm('削除しますか？')) return
  await $fetch(`/api/family/${id}`, { method: 'DELETE' })
  await fetchPerson()
}

async function addEvent() {
  await $fetch('/api/events', {
    method: 'POST',
    body: { ...newEvent.value, personId: Number(route.params.id) },
  })
  showEventModal.value = false
  newEvent.value = { eventDate: '', content: '' }
  await fetchPerson()
}

async function deleteEvent(id: number) {
  if (!confirm('削除しますか？')) return
  await $fetch(`/api/events/${id}`, { method: 'DELETE' })
  await fetchPerson()
}

function formatBirthday(birthday: string) {
  if (!birthday) return ''
  const [y, m, d] = birthday.split('-').map(Number)
  const today = new Date()
  let age = today.getFullYear() - y
  if (today.getMonth() + 1 < m || (today.getMonth() + 1 === m && today.getDate() < d)) age--
  return `${m}/${d} (${age}歳)`
}

function formatEventDate(date: string) {
  if (!date) return ''
  const [y, m, d] = date.split('-').map(Number)
  return `${y}年${m}月${d}日`
}

onMounted(fetchPerson)
</script>
