<template>
  <div class="mobile-top-sidenav">
    <div class="row">
      <div class="col-8">
        <WidgetsBrandLogo />
      </div>
      <div class="col-4">
        <div class="back-btn">
          <div class="mobile-back text-end">
            <img @click="openmobilenav()" src="/images/new_evacode/close_sidenav_icon.svg" alt="close_sidenav_icon" />
          </div>
        </div>
      </div>
    </div>
    <div class="row phone-and-cart-row">
      <div class="col-10">
        <div class="top-sidenav-cur-phone top-header-v-centered">
          <WidgetsCurrency />
          <WidgetsContactPhone />
        </div>
      </div>
      <div class="col-2">
        <WidgetsHeaderWidgets/>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  props: ['leftSidebarVal', 'openmobilenav'],
}
</script>

<style scoped>

</style>
