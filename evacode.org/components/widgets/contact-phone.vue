<template>
  <a
    class="header-account header-contact"
    href="#footer-contacts"
    aria-label="Контакты"
    @click.prevent="goToContacts"
  >
    <div class="top-header-shopping-cart">
      <span class="header-account__icon">
        <svg class="img-fluid" viewBox="0 0 24 24" aria-hidden="true">
          <path
            d="M6.62 10.79a15.15 15.15 0 006.59 6.59l2.2-2.2a1 1 0 011.01-.24c1.12.37 2.33.57 3.58.57a1 1 0 011 1V20a1 1 0 01-1 1C10.4 21 3 13.6 3 4a1 1 0 011-1h3.5a1 1 0 011 1c0 1.25.2 2.46.57 3.58a1 1 0 01-.25 1.02l-2.2 2.19z"
          />
        </svg>
      </span>
      <span class="shopping-cart-text">Контакты</span>
    </div>
  </a>
</template>

<script setup>
const goToContacts = async () => {
  if (!import.meta.client) {
    return;
  }

  let el = document.getElementById('footer-contacts');
  if (!el) {
    await navigateTo({ hash: 'footer-contacts' });
    await nextTick();
    el = document.getElementById('footer-contacts');
  }

  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    if (window.location.hash !== '#footer-contacts') {
      history.replaceState(null, '', '#footer-contacts');
    }
  }
};
</script>
