<template>
  <div>
    <header>
      <WidgetsTopbar />
      <section v-if="showMenu" class="header-menu-section">
        <div class="container">
          <div class="row">
            <div class="col-12">
                <WidgetsNavbar />
            </div>
          </div>
        </div>
      </section>
    </header>
  </div>
</template>

<script setup>
const props = defineProps({
    showMenu:{
        type: Boolean,
        default: true,
    },
});
</script>

<style scoped>
  .brand-logo img {
    width: auto;
  }
</style>
