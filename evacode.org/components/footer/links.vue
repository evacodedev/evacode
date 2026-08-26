<template>
  <div>
      <ul class="footer-links">
          <li v-for="(menuItem, index) in footerMenu.data" :key="index">
              <nuxt-link :to="menuItem.path"> {{menuItem.title}} </nuxt-link>
          </li>
      </ul>
  </div>
</template>

<script setup>
import footerMenu from '../../data/footerMenu.json'
</script>
