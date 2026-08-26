<template>
  <div class="brand-logo">
    <nuxt-link :to="{ path: '/' }">
      <img :src="logo_type === 'white' ? '/images/new_evacode/evacode_slide_white_logo.svg' : '/images/new_evacode/evacode_header_logo.svg'" />
    </nuxt-link>
  </div>
</template>

<script setup>
const props = defineProps({
  logo_type: {
    type: String,
    default: 'black',
  },
});

</script>
