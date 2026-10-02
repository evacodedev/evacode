<template>
<Header/>
  <div>
   <PaymentPage/>
  </div>
  <Footer />
</template>
<script setup>
definePageMeta({
  middleware: 'checkout-consultant',
})

useHead({
  titleTemplate: `%s - Оформить заказ`,
  meta: [
    {
      name: 'description',
      content: 'Оформление заказа EvaCode'
    },
  ]
});
useNoIndex();

</script>
