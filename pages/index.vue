<template>
  <div v-if="checking" class="min-h-screen bg-bg-primary flex items-center justify-center">
    <p class="text-text-muted">Loading...</p>
  </div>

  <!-- Login -->
  <div v-else-if="!authenticated" class="min-h-screen bg-bg-primary flex items-center justify-center">
    <div class="w-full max-w-sm px-6">
      <h1 class="font-serif text-5xl text-center text-text-primary mb-12">People Wiki</h1>
      <form @submit.prevent="handleLogin" class="space-y-4">
        <input
          v-model="password"
          type="password"
          placeholder="Password"
          class="w-full bg-bg-card border border-border rounded-lg px-4 py-3 text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent transition-colors"
        />
        <p v-if="loginError" class="text-danger text-sm">{{ loginError }}</p>
        <button
          type="submit"
          class="w-full bg-accent hover:bg-accent-hover text-bg-primary font-medium rounded-lg py-3 transition-colors"
        >
          Enter
        </button>
      </form>
    </div>
  </div>

  <!-- People List -->
  <NuxtLayout v-else name="default">
    <div class="space-y-8">
      <!-- Hero -->
      <div class="border-b border-border pb-8">
        <h1 class="font-serif text-6xl text-text-primary mb-6">People</h1>
        <div class="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
          <!-- Search -->
          <div class="relative flex-1 max-w-md">
            <input
              v-model="search"
              type="text"
              placeholder="Search..."
              class="w-full bg-bg-card border border-border rounded-lg pl-10 pr-4 py-2.5 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent transition-colors"
              @input="debouncedFetch"
            />
            <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
            </svg>
          </div>
          <div class="flex gap-3 items-center">
            <!-- Sort -->
            <div class="flex text-sm">
              <span class="text-text-muted mr-2">Sort by:</span>
              <button
                @click="sort = 'updated'; fetchPeople()"
                :class="sort === 'updated' ? 'text-text-primary' : 'text-text-muted hover:text-text-secondary'"
                class="transition-colors"
              >
                Updated
              </button>
              <span class="text-border mx-2">|</span>
              <button
                @click="sort = 'birthday'; fetchPeople()"
                :class="sort === 'birthday' ? 'text-text-primary' : 'text-text-muted hover:text-text-secondary'"
                class="transition-colors"
              >
                Birthday
              </button>
            </div>
            <!-- Add -->
            <button
              @click="showAddModal = true"
              class="bg-accent hover:bg-accent-hover text-bg-primary text-sm font-medium rounded-lg px-4 py-2.5 transition-colors"
            >
              + Add Person
            </button>
          </div>
        </div>
      </div>

      <!-- Grid -->
      <div v-if="people.length" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <NuxtLink
          v-for="person in people"
          :key="person.id"
          :to="`/people/${person.id}`"
          class="group bg-bg-card border border-border rounded-lg p-5 hover:border-border-light hover:bg-bg-hover transition-all"
        >
          <div class="flex items-start gap-4">
            <div class="w-12 h-12 rounded-full bg-bg-hover flex items-center justify-center text-text-muted font-serif text-lg shrink-0 overflow-hidden">
              <img v-if="person.imageUrl" :src="person.imageUrl" :alt="person.name" class="w-full h-full object-cover" />
              <span v-else>{{ person.name[0] }}</span>
            </div>
            <div class="min-w-0">
              <h3 class="font-medium text-text-primary group-hover:text-accent transition-colors truncate">
                {{ person.name }}
              </h3>
              <p v-if="person.organization" class="text-sm text-text-secondary truncate mt-0.5">
                {{ person.organization }}
              </p>
              <p v-if="person.birthday" class="text-xs text-text-muted mt-1">
                {{ formatBirthday(person.birthday) }}
              </p>
            </div>
          </div>
          <p v-if="person.notes" class="text-sm text-text-muted mt-3 line-clamp-2">
            {{ person.notes }}
          </p>
        </NuxtLink>
      </div>

      <div v-else class="text-center py-20">
        <p class="text-text-muted font-serif text-2xl">No people yet</p>
        <p class="text-text-muted text-sm mt-2">Add your first person to get started</p>
      </div>
    </div>

    <!-- Add Person Modal -->
    <Teleport to="body">
      <div v-if="showAddModal" class="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4" @click.self="showAddModal = false">
        <div class="bg-bg-secondary border border-border rounded-xl w-full max-w-lg max-h-[90vh] overflow-y-auto p-6">
          <h2 class="font-serif text-2xl text-text-primary mb-6">New Person</h2>
          <form @submit.prevent="addPerson" class="space-y-4">
            <div>
              <label class="block text-sm text-text-secondary mb-1">Name *</label>
              <input v-model="newPerson.name" required class="w-full bg-bg-card border border-border rounded-lg px-4 py-2.5 text-text-primary focus:outline-none focus:border-accent transition-colors" />
            </div>
            <div>
              <label class="block text-sm text-text-secondary mb-1">Organization</label>
              <input v-model="newPerson.organization" class="w-full bg-bg-card border border-border rounded-lg px-4 py-2.5 text-text-primary focus:outline-none focus:border-accent transition-colors" />
            </div>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm text-text-secondary mb-1">Birthday</label>
                <input v-model="newPerson.birthday" type="date" class="w-full bg-bg-card border border-border rounded-lg px-4 py-2.5 text-text-primary focus:outline-none focus:border-accent transition-colors" />
              </div>
              <div>
                <label class="block text-sm text-text-secondary mb-1">Met at</label>
                <input v-model="newPerson.metAt" class="w-full bg-bg-card border border-border rounded-lg px-4 py-2.5 text-text-primary focus:outline-none focus:border-accent transition-colors" />
              </div>
            </div>
            <div>
              <label class="block text-sm text-text-secondary mb-1">Notes</label>
              <textarea v-model="newPerson.notes" rows="3" class="w-full bg-bg-card border border-border rounded-lg px-4 py-2.5 text-text-primary focus:outline-none focus:border-accent transition-colors resize-none" />
            </div>
            <div class="flex gap-3 pt-2">
              <button type="button" @click="showAddModal = false" class="flex-1 border border-border text-text-secondary rounded-lg py-2.5 hover:bg-bg-hover transition-colors">
                Cancel
              </button>
              <button type="submit" :disabled="!newPerson.name" class="flex-1 bg-accent hover:bg-accent-hover disabled:opacity-40 text-bg-primary font-medium rounded-lg py-2.5 transition-colors">
                Add
              </button>
            </div>
          </form>
        </div>
      </div>
    </Teleport>
  </NuxtLayout>
</template>

<script setup lang="ts">
const { authenticated, checking, check, login } = useAuth()
const password = ref('')
const loginError = ref('')

const search = ref('')
const sort = ref('updated')
const people = ref<any[]>([])
const showAddModal = ref(false)
const newPerson = ref({ name: '', organization: '', birthday: '', metAt: '', notes: '' })

let debounceTimer: ReturnType<typeof setTimeout>
function debouncedFetch() {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => fetchPeople(), 300)
}

async function handleLogin() {
  loginError.value = ''
  try {
    await login(password.value)
    await fetchPeople()
  } catch {
    loginError.value = 'パスワードが正しくありません'
  }
}

async function fetchPeople() {
  try {
    people.value = await $fetch('/api/people', {
      query: { q: search.value, sort: sort.value },
    })
  } catch {}
}

async function addPerson() {
  await $fetch('/api/people', { method: 'POST', body: newPerson.value })
  showAddModal.value = false
  newPerson.value = { name: '', organization: '', birthday: '', metAt: '', notes: '' }
  await fetchPeople()
}

function formatBirthday(birthday: string) {
  if (!birthday) return ''
  const [y, m, d] = birthday.split('-').map(Number)
  const today = new Date()
  let age = today.getFullYear() - y
  if (today.getMonth() + 1 < m || (today.getMonth() + 1 === m && today.getDate() < d)) age--
  return `${m}/${d} (${age}歳)`
}

onMounted(async () => {
  await check()
  if (authenticated.value) await fetchPeople()
})
</script>
