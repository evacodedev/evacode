<template>
  <Teleport to="body">
    <div class="app-notice" role="status" aria-live="polite">
      <Transition name="app-notice">
        <p v-if="notice.text" :key="notice.id" class="app-notice__text">{{ notice.text }}</p>
      </Transition>
    </div>
  </Teleport>
</template>

<script setup>
const { notice } = useAppNotice()
</script>
