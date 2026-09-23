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
      <section v-if="showMenu" class="header-catalog">
        <div class="container">
          <div class="header-catalog__panel">
            <WidgetsCatalogFilters global />
          </div>
        </div>
      </section>
    </header>
  </div>
</template>

<script setup>
defineProps({
    showMenu: {
        type: Boolean,
        default: true,
    },
});
</script>

<style scoped>
  .brand-logo img {
    width: auto;
  }

  header :deep(.top-header) {
    position: relative;
    z-index: 40;
  }

  .header-menu-section {
    position: relative;
    z-index: 10;
  }

  .header-catalog {
    position: relative;
    z-index: 5;
    padding: 16px 0 18px;
    background: #f7f4ef;
    border-bottom: 1px solid #ece8e1;
  }

  .header-catalog__panel {
    padding: 14px 18px;
    background: #fff;
    border: 1px solid #ece8e1;
    border-radius: 8px;
  }

  .header-catalog__panel :deep(.catalog-bar-wrap) {
    margin-bottom: 0;
  }

  .header-catalog__panel :deep(.catalog-bar) {
    border-bottom: 0;
    min-height: 0;
    padding: 0;
    gap: 16px 24px;
  }

  .header-catalog__panel :deep(.catalog-bar__chips) {
    margin-top: 12px;
    padding-bottom: 0;
  }
</style>
