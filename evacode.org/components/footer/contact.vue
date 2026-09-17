<template>
  <div v-if="contacts">
    <ul class="contact-list">
      <li>
        <i class="fa fa-map-marker"></i>
        <div v-html="contacts.address"></div>
      </li>
    </ul>
    <WidgetsMessengerLinks
      variant="footer"
      :phone="contacts.phone"
      :phone-href="'tel:' + contacts.phone"
      :email="contacts.email"
    />
  </div>
</template>

<script setup>
import {useContactsStore} from '~~/store/contacts'
const contacts = ref(null);

onMounted(async () => {
  contacts.value = await useContactsStore().contacts;
});
</script>

<style scoped>
ul.contact-list  li {
  text-transform: none;
}
</style>
