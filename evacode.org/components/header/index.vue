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
      <template v-if="showMenu">
        <div ref="catalogSentinel" class="header-catalog-sentinel" aria-hidden="true" />
        <div
          v-if="catalogStuck"
          class="header-catalog-spacer"
          :style="{ height: `${catalogHeight}px` }"
          aria-hidden="true"
        />
        <section
          ref="catalogEl"
          class="header-catalog"
          :class="{ 'is-stuck': catalogStuck }"
        >
          <div class="container">
            <div class="header-catalog__panel">
              <WidgetsCatalogFilters global />
            </div>
          </div>
        </section>
      </template>
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

const catalogSentinel = ref(null);
const catalogEl = ref(null);
const catalogStuck = ref(false);
const catalogHeight = ref(0);

let observer = null;

const measureCatalog = () => {
    if (!catalogEl.value) {
        return;
    }
    catalogHeight.value = catalogEl.value.offsetHeight;
};

onMounted(() => {
    if (!import.meta.client || !catalogSentinel.value) {
        return;
    }

    measureCatalog();

    observer = new IntersectionObserver(
        ([entry]) => {
            measureCatalog();
            catalogStuck.value = !entry.isIntersecting;
        },
        { threshold: 0 },
    );
    observer.observe(catalogSentinel.value);
    window.addEventListener('resize', measureCatalog, { passive: true });
});

onBeforeUnmount(() => {
    observer?.disconnect();
    if (import.meta.client) {
        window.removeEventListener('resize', measureCatalog);
    }
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

  .header-catalog-sentinel {
    height: 0;
    width: 100%;
    pointer-events: none;
  }

  .header-catalog-spacer {
    width: 100%;
    pointer-events: none;
  }

  .header-catalog {
    position: relative;
    z-index: 5;
    padding: 16px 0 18px;
    background: #f7f4ef;
    border-bottom: 1px solid #ece8e1;
  }

  .header-catalog.is-stuck {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 90;
    padding-top: max(10px, env(safe-area-inset-top, 0px));
    padding-bottom: 10px;
  }

  .header-catalog.is-stuck :deep(.catalog-bar-wrap) {
    z-index: 30;
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

  @media (max-width: 991px) {
    .header-catalog {
      padding: 0;
    }

    .header-catalog.is-stuck {
      padding-top: env(safe-area-inset-top, 0px);
      padding-bottom: 0;
    }

    .header-catalog :deep(.container) {
      max-width: none;
      width: 100%;
      padding-left: 0;
      padding-right: 0;
    }

    .header-catalog__panel {
      padding: 6px 10px;
      border-radius: 0;
      border-left: 0;
      border-right: 0;
    }

    .header-catalog__panel :deep(.catalog-bar) {
      gap: 8px;
      min-height: 0;
      padding: 0;
    }

    .header-catalog__panel :deep(.catalog-bar__chips) {
      margin-top: 6px;
    }

    .header-catalog__panel :deep(.catalog-pop) {
      left: 10px;
      right: 10px;
      width: auto;
      max-width: none;
    }
  }
</style>
