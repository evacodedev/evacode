<template>
  <div>
    <Header />
    <AccountShell current="addresses">
      <h2 class="account-lux__heading">Адреса доставки</h2>
      <AccountEmpty
        lead="Сохранённых адресов нет."
        text="Адрес можно указать при оформлении заказа — в том числе как гость."
      />
    </AccountShell>
    <Footer />
  </div>
</template>

<script setup>
definePageMeta({
  middleware: 'account-auth',
})

useHead({
  titleTemplate: '%s — Адреса',
})
</script>
