<template>
  <ul v-if="contacts" class="contact-list">
    <li><i class="fa fa-map-marker"></i><div v-html="contacts.address"></div>
    </li>
    <li><i class="fa fa-phone"></i>Телефон: <phone-link :phone="contacts.phone"/></li>
    <li><i class="fa fa-envelope"></i>Email Us: <mail-link :email="contacts.email"/></li>
    <li class="contact-list__messengers">
      <WidgetsMessengerLinks variant="footer"/>
    </li>
  </ul>
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
