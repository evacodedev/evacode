<template>
  <Teleport to="body">
    <div
      v-if="open"
      class="app-handoff"
      role="alertdialog"
      aria-modal="true"
      aria-labelledby="app-handoff-title"
      aria-busy="true"
    >
      <div class="app-handoff__card">
        <span class="app-handoff__icon" aria-hidden="true">
          <svg v-if="variant === 'checkout'" viewBox="0 0 48 48" fill="none">
            <circle class="app-handoff__track" cx="24" cy="24" r="22.5" stroke="currentColor" stroke-width="1.25"/>
            <g class="app-handoff__spin">
              <circle cx="24" cy="24" r="22.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-dasharray="36 108"/>
            </g>
            <path d="M16 20h16l-1.2 14.4A2 2 0 0 1 28.81 36H19.19a2 2 0 0 1-1.99-1.6L16 20Z" stroke="currentColor" stroke-width="1.4"/>
            <path d="M19 20v-3.2A5 5 0 0 1 24 12a5 5 0 0 1 5 4.8V20" stroke="currentColor" stroke-width="1.4"/>
          </svg>
          <svg v-else viewBox="0 0 48 48" fill="none">
            <circle class="app-handoff__track" cx="24" cy="24" r="18" stroke="currentColor" stroke-width="1.25"/>
            <g class="app-handoff__spin">
              <circle cx="24" cy="24" r="18" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-dasharray="28 86"/>
            </g>
          </svg>
        </span>
        <p id="app-handoff-title" class="app-handoff__title">{{ title }}</p>
        <p v-if="note" class="app-handoff__note">{{ note }}</p>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
const { open, title, note, variant } = useHandoff()

watch(
  open,
  (isOpen) => {
    if (!process.client) {
      return
    }
    document.documentElement.classList.toggle('app-handoff-open', Boolean(isOpen))
  },
  { immediate: true },
)

onBeforeUnmount(() => {
  if (process.client) {
    document.documentElement.classList.remove('app-handoff-open')
  }
})
</script>
