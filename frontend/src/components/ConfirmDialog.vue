<template>
  <div class="document-preview-modal" role="dialog" aria-modal="true">
    <div class="duplicate-upload-dialog">
      <header class="duplicate-upload-head">
        <div>
          <strong>{{ title }}</strong>
          <p>{{ message }}</p>
        </div>
        <button class="icon-button" title="关闭" aria-label="关闭" @click="$emit('cancel')">×</button>
      </header>

      <div class="duplicate-upload-body">
        <article class="duplicate-match">
          <div>
            <strong>{{ prompt }}</strong>
            <span>{{ subjectLabel }}</span>
          </div>
          <small>{{ detail }}</small>
        </article>
      </div>

      <footer class="duplicate-upload-actions">
        <button @click="$emit('cancel')">{{ cancelText }}</button>
        <button class="danger" :disabled="busy" @click="$emit('confirm')">
          {{ confirmText }}
        </button>
      </footer>
    </div>
  </div>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    title: string
    message: string
    subjectLabel: string
    detail?: string
    prompt?: string
    cancelText?: string
    confirmText?: string
    busy?: boolean
  }>(),
  {
    detail: '取消不会影响当前选择，确认后将执行删除操作。',
    prompt: '请确认是否继续删除',
    cancelText: '取消',
    confirmText: '确认删除',
    busy: false
  }
)

defineEmits<{
  cancel: []
  confirm: []
}>()
</script>
