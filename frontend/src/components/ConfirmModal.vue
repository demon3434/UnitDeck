<template>
  <dialog :class="['modal modal-bottom sm:modal-middle', { 'modal-open': isOpen }]">
    <div class="modal-box bg-base-100 border border-base-content/10 shadow-2xl">
      <h3 class="font-bold text-lg flex items-center gap-2">
        <component :is="iconComponent" :class="iconClass" class="w-5 h-5" />
        <span>{{ title }}</span>
      </h3>
      
      <p class="py-4 text-base-content/80 text-sm whitespace-pre-line leading-relaxed">
        {{ message }}
      </p>

      <div v-if="targetName" class="badge badge-lg badge-neutral font-mono mb-4">
        {{ targetName }}
      </div>

      <div class="modal-action">
        <button 
          class="btn btn-ghost btn-sm" 
          @click="onCancel"
          :disabled="loading"
        >
          取消
        </button>
        <button 
          :class="['btn btn-sm', confirmBtnClass]" 
          @click="onConfirm"
          :disabled="loading"
        >
          <span v-if="loading" class="loading loading-spinner loading-xs"></span>
          {{ confirmText }}
        </button>
      </div>
    </div>
    <form method="dialog" class="modal-backdrop" @click="onCancel">
      <button>关闭</button>
    </form>
  </dialog>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { AlertTriangle, Power, RefreshCw, Trash2, ShieldAlert } from 'lucide-vue-next';

const props = withDefaults(
  defineProps<{
    isOpen: boolean;
    title?: string;
    message?: string;
    targetName?: string;
    actionType?: 'start' | 'stop' | 'restart' | 'stop-all' | 'clean' | 'enable' | 'disable' | 'danger';
    confirmText?: string;
    loading?: boolean;
  }>(),
  {
    title: '确认操作',
    message: '您确定要继续此操作吗？',
    targetName: '',
    actionType: 'start',
    confirmText: '确定',
    loading: false,
  }
);

const emit = defineEmits<{
  (e: 'confirm'): void;
  (e: 'cancel'): void;
}>();

const iconComponent = computed(() => {
  switch (props.actionType) {
    case 'stop':
    case 'stop-all':
      return Power;
    case 'restart':
      return RefreshCw;
    case 'clean':
      return Trash2;
    case 'danger':
      return ShieldAlert;
    default:
      return AlertTriangle;
  }
});

const iconClass = computed(() => {
  switch (props.actionType) {
    case 'stop':
    case 'stop-all':
    case 'danger':
      return 'text-error';
    case 'start':
    case 'enable':
      return 'text-success';
    case 'restart':
      return 'text-warning';
    default:
      return 'text-info';
  }
});

const confirmBtnClass = computed(() => {
  switch (props.actionType) {
    case 'stop':
    case 'stop-all':
    case 'danger':
      return 'btn-error';
    case 'start':
    case 'enable':
      return 'btn-success';
    case 'restart':
      return 'btn-warning';
    default:
      return 'btn-primary';
  }
});

function onConfirm() {
  emit('confirm');
}

function onCancel() {
  if (!props.loading) {
    emit('cancel');
  }
}
</script>

