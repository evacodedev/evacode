<template>
  <div>
    <!-- Sample menu definition -->
    <div class="main-navbar">
      <div class="mainnav">
        <div class="toggle-nav" :class="leftSidebarVal ? 'toggle-button' : ''" @click="openMobileNavProp = true">
          <img alt src="/images/new_evacode/hamburger_menu_icon.svg" class="img-fluid">
        </div>
        <ul class="nav-menu" :class="{ opennav: openMobileNavProp }">
          <MobileTopSidenav
              :openmobilenav = "openmobilenav"
          />
          <li v-for="(menuItem, index) in menulist" :key="index" class="'dropdown'">
            <nuxt-link :to="menuItem.path"> {{menuItem.title}} </nuxt-link>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script>
import { mapState } from 'pinia'
import { useMenuStore } from '~/store/menu'
import MobileTopSidenav from '~/components/widgets/mobile-top-sidenav.vue';
export default {
  components: {MobileTopSidenav},
  props: ['leftSidebarVal'],
  data() {
    return {
      openMobileNavProp: false,
    }
  },
  computed: {
    ...mapState(useMenuStore, {
      menulist: 'data'
    })
  },
  methods: {
    openmobilenav() {
      this.openMobileNavProp = !this.openMobileNavProp;
    }
  }
}
</script>

<style lang="scss" scoped>
.toggle-nav {
  &.toggle-button {
    z-index: 1;
  }
}
.router-link-exact-active {
  color: var(--theme-deafult);
}
</style>
