<template>
  <div class="account-lux__empty">
    <p class="account-lux__empty-lead">{{ lead }}</p>
    <p v-if="text || $slots.default" class="account-lux__empty-text">
      <slot>{{ text }}</slot>
    </p>
    <nuxt-link v-if="to" :to="to" class="account-lux__ghost">{{ cta }}</nuxt-link>
  </div>
</template>

<script setup>
defineProps({
  lead: { type: String, required: true },
  text: { type: String, default: '' },
  cta: { type: String, default: 'В каталог' },
  to: { type: String, default: '' },
})
</script>
