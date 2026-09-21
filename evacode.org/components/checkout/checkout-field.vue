<template>
  <div
    class="checkout-field"
    :class="{
      'is-filled': filled,
      'is-focused': focused,
      'is-invalid': showError,
      'is-select': Boolean(options),
      'is-password': isPassword,
      'is-textarea': isTextarea,
      'is-disabled': disabled,
    }"
  >
    <select
      v-if="options"
      :id="inputId"
      v-model="selected"
      :name="name"
      :autocomplete="autocomplete"
      @focus="focused = true"
      @blur="onBlur"
    >
      <option disabled value=""></option>
      <option
        v-for="option in options"
        :key="String(option.value)"
        :value="option.value"
      >
        {{ option.label }}
      </option>
    </select>
    <textarea
      v-else-if="isTextarea"
      :id="inputId"
      :value="modelValue"
      :autocomplete="autocomplete"
      :name="name"
      :disabled="disabled"
      :rows="rows"
      placeholder=" "
      @input="onInput"
      @focus="focused = true"
      @blur="onBlur"
    />
    <input
      v-else
      :id="inputId"
      :type="inputType"
      :value="modelValue"
      :autocomplete="autocomplete"
      :name="name"
      :disabled="disabled"
      :inputmode="inputMode"
      placeholder=" "
      @input="onInput"
      @focus="focused = true"
      @blur="onBlur"
    >
    <label :for="inputId">{{ label }}</label>
    <button
      v-if="isPassword"
      class="checkout-field__reveal"
      type="button"
      :aria-label="revealed ? 'Скрыть пароль' : 'Показать пароль'"
      :aria-pressed="revealed"
      @mousedown.prevent
      @click="revealed = !revealed"
    >
      <svg v-if="revealed" viewBox="0 0 24 24" aria-hidden="true">
        <path d="M3 3l18 18" />
        <path d="M10.6 10.6A3 3 0 0012 15a3 3 0 002.4-4.4" />
        <path d="M9.9 5.2A10.8 10.8 0 0112 5c6.5 0 10 7 10 7a17.6 17.6 0 01-3.2 3.9" />
        <path d="M6.1 6.1C3.8 7.8 2 12 2 12s3.5 7 10 7c1.7 0 3.2-.4 4.5-1" />
      </svg>
      <svg v-else viewBox="0 0 24 24" aria-hidden="true">
        <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z" />
        <circle cx="12" cy="12" r="3" />
      </svg>
    </button>
    <p v-if="showError" class="checkout-field__error">{{ error }}</p>
  </div>
</template>

<script>
import { maskPhoneRu, maskTelegram } from '~/utils/input-mask'

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
    disabled: { type: Boolean, default: false },
    mask: { type: String, default: '' },
    rows: { type: Number, default: 3 },
  },
  emits: ['update:modelValue', 'blur'],
  data() {
    return {
      focused: false,
      touched: false,
      revealed: false,
    }
  },
  computed: {
    inputId() {
      return `checkout-${this.name || this.label}`
    },
    isPassword() {
      return this.type === 'password'
    },
    isTextarea() {
      return this.type === 'textarea'
    },
    inputType() {
      if (this.isPassword && this.revealed) {
        return 'text'
      }
      return this.type
    },
    inputMode() {
      if (this.mask === 'phone' || this.type === 'tel') {
        return 'tel'
      }
      return undefined
    },
    selected: {
      get() {
        return this.modelValue
      },
      set(value) {
        this.$emit('update:modelValue', value)
      },
    },
    filled() {
      return String(this.modelValue || '').trim().length > 0
    },
    showError() {
      return Boolean(this.error) && (this.touched || this.submitted)
    },
  },
  methods: {
    maskedValue(value) {
      if (this.mask === 'phone') {
        return maskPhoneRu(value)
      }
      if (this.mask === 'telegram') {
        return maskTelegram(value)
      }
      return value
    },
    onInput(event) {
      this.$emit('update:modelValue', this.maskedValue(event.target.value))
    },
    onBlur() {
      this.focused = false
      this.touched = true
      this.$emit('blur')
    },
  },
}
</script>
