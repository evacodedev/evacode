<template>
  <div class="account-lux__empty" :class="{ 'is-illustrated': Boolean(icon) }">
    <span v-if="icon" class="account-lux__empty-icon" aria-hidden="true">
      <svg viewBox="0 0 48 48" fill="none">
        <circle class="account-lux__empty-track" cx="24" cy="24" r="22.5" stroke="currentColor" stroke-width="1.25"/>
        <g v-if="icon === 'bag'">
          <path d="M16 20h16l-1.2 14.4A2 2 0 0 1 28.81 36H19.19a2 2 0 0 1-1.99-1.6L16 20Z" stroke="currentColor" stroke-width="1.4"/>
          <path d="M19 20v-3.2A5 5 0 0 1 24 12a5 5 0 0 1 5 4.8V20" stroke="currentColor" stroke-width="1.4"/>
        </g>
        <path
          v-else-if="icon === 'heart'"
          d="M24 34.2s-8.2-5.2-8.2-10.8A4.9 4.9 0 0 1 24 18.6a4.9 4.9 0 0 1 8.2 4.8C32.2 29 24 34.2 24 34.2Z"
          stroke="currentColor"
          stroke-width="1.4"
          stroke-linejoin="round"
        />
      </svg>
    </span>
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
  icon: { type: String, default: '' },
})
</script>
