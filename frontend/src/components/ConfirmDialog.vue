<!-- 通用确认弹窗：用于删除、批量操作等需要二次确认的危险动作。 -->

<template>
  <div class="document-preview-modal confirm-dialog-modal" role="dialog" aria-modal="true" aria-labelledby="confirm-title">
    <section class="confirm-dialog" @click.stop>
      <header>
        <div>
          <strong id="confirm-title">{{ title }}</strong>
          <span v-if="subjectLabel">{{ subjectLabel }}</span>
        </div>
      </header>

      <div class="confirm-dialog-body">
        <p>{{ message }}</p>
        <p v-if="detail" class="confirm-dialog-detail">{{ detail }}</p>
      </div>

      <footer>
        <button type="button" :disabled="busy" @click="$emit('cancel')">取消</button>
        <button type="button" class="danger" :disabled="busy" @click="$emit('confirm')">
          {{ busy ? '处理中' : '确认' }}
        </button>
      </footer>
    </section>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title: string
  message: string
  subjectLabel?: string
  detail?: string
  busy?: boolean
}>()

defineEmits<{
  cancel: []
  confirm: []
}>()
</script>
