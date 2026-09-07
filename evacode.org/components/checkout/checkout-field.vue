<template>
  <div
    class="checkout-field"
    :class="{
      'is-filled': filled,
      'is-focused': focused,
      'is-invalid': showError,
      'is-select': Boolean(options),
    }"
  >
    <select
      v-if="options"
      :id="inputId"
      :value="modelValue"
      :name="name"
      :autocomplete="autocomplete"
      @change="$emit('update:modelValue', $event.target.value)"
      @focus="focused = true"
      @blur="onBlur"
    >
      <option value="" disabled hidden></option>
      <option
        v-for="option in options"
        :key="option.value"
        :value="option.value"
      >
        {{ option.label }}
      </option>
    </select>
    <input
      v-else
      :id="inputId"
      :type="type"
      :value="modelValue"
      :autocomplete="autocomplete"
      :name="name"
      placeholder=" "
      @input="$emit('update:modelValue', $event.target.value)"
      @focus="focused = true"
      @blur="onBlur"
    >
    <label :for="inputId">{{ label }}</label>
    <p v-if="showError" class="checkout-field__error">{{ error }}</p>
  </div>
</template>

<script>
export default {
  name: 'CheckoutField',
  props: {
    modelValue: { type: String, default: '' },
    label: { type: String, required: true },
    error: { type: String, default: '' },
    submitted: { type: Boolean, default: false },
    type: { type: String, default: 'text' },
    autocomplete: { type: String, default: 'off' },
    name: { type: String, default: '' },
    options: { type: Array, default: null },
  },
  emits: ['update:modelValue', 'blur'],
  data() {
    return {
      focused: false,
      touched: false,
    }
  },
  computed: {
    inputId() {
      return `checkout-${this.name || this.label}`
    },
    filled() {
      return String(this.modelValue || '').trim().length > 0
    },
    showError() {
      return Boolean(this.error) && (this.touched || this.submitted)
    },
  },
  methods: {
    onBlur() {
      this.focused = false
      this.touched = true
      this.$emit('blur')
    },
  },
}
</script>
