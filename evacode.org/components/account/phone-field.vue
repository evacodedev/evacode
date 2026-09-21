<template>
  <div class="account-phone">
    <MazPhoneNumberInput
      :id="inputId"
      :model-value="modelValue"
      :default-country-code="empty ? 'KR' : undefined"
      :preferred-countries="preferredCountries"
      :translations="translations"
      country-locale="ru-RU"
      country-selector-width="148px"
      orientation="row"
      size="xl"
      show-code-on-list
      no-example
      no-validation-error
      no-validation-success
      no-use-browser-locale
      block
      @update:model-value="$emit('update:modelValue', $event || '')"
    />
  </div>
</template>

<script>
import MazPhoneNumberInput from 'maz-ui/components/MazPhoneNumberInput'
import { PHONE_PREFERRED_COUNTRIES } from '~/utils/input-mask'

export default {
  name: 'AccountPhoneField',
  components: { MazPhoneNumberInput },
  props: {
    modelValue: { type: String, default: '' },
    label: { type: String, required: true },
    name: { type: String, default: '' },
  },
  emits: ['update:modelValue'],
  computed: {
    inputId() {
      return `account-${this.name || this.label}`
    },
    empty() {
      return !String(this.modelValue || '').trim()
    },
    preferredCountries() {
      return PHONE_PREFERRED_COUNTRIES
    },
    translations() {
      return {
        countrySelector: {
          placeholder: 'Код',
          error: 'Выберите страну',
          searchPlaceholder: 'Страна',
        },
        phoneInput: {
          placeholder: this.label,
          example: '',
        },
      }
    },
  },
}
</script>
