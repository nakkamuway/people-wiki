<template>
  <div class="min-h-screen bg-bg-primary text-text-primary font-sans">
    <!-- Header -->
    <header class="border-b border-border">
      <div class="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
        <NuxtLink to="/" class="font-serif text-2xl text-text-primary hover:text-accent transition-colors">
          People Wiki
        </NuxtLink>
        <nav class="flex items-center gap-6">
          <NuxtLink
            to="/"
            class="text-sm tracking-widest uppercase text-text-secondary hover:text-text-primary transition-colors"
          >
            People
          </NuxtLink>
          <button
            @click="handleLogout"
            class="text-sm tracking-widest uppercase text-text-muted hover:text-text-primary transition-colors"
          >
            Logout
          </button>
        </nav>
      </div>
    </header>

    <!-- Content -->
    <main class="max-w-6xl mx-auto px-6 py-10">
      <slot />
    </main>
  </div>
</template>

<script setup lang="ts">
const { logout } = useAuth()

async function handleLogout() {
  await logout()
}
</script>
