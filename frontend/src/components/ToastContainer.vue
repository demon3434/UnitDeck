<template>
  <div class="toast toast-top toast-end z-[9999] pointer-events-none p-4 space-y-2">
    <transition-group
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="transform translate-y-2 opacity-0 scale-95"
      enter-to-class="transform translate-y-0 opacity-100 scale-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="transform translate-y-0 opacity-100 scale-100"
      leave-to-class="transform translate-y-2 opacity-0 scale-95"
    >
      <div
        v-for="t in toastStore.toasts"
        :key="t.id"
        :class="[
          'alert shadow-xl text-xs sm:text-sm flex items-center gap-2.5 pointer-events-auto border backdrop-blur-md rounded-xl py-2.5 px-4',
          alertClass(t.type)
        ]"
      >
        <CheckCircle2 v-if="t.type === 'success'" class="w-4 h-4 shrink-0 text-success" />
        <AlertCircle v-else-if="t.type === 'error'" class="w-4 h-4 shrink-0 text-error" />
        <AlertTriangle v-else-if="t.type === 'warning'" class="w-4 h-4 shrink-0 text-warning" />
        <Info v-else class="w-4 h-4 shrink-0 text-info" />
        <span class="font-medium">{{ t.message }}</span>
        <button 
          class="btn btn-ghost btn-xs btn-circle ml-1 opacity-70 hover:opacity-100" 
          @click="toastStore.remove(t.id)"
        >
          ✕
        </button>
      </div>
    </transition-group>
  </div>
</template>

<script setup lang="ts">
import { CheckCircle2, AlertCircle, AlertTriangle, Info } from 'lucide-vue-next';
import { useToastStore } from '../stores/toast';

const toastStore = useToastStore();

function alertClass(type: string) {
  switch (type) {
    case 'success':
      return 'bg-base-100/95 border-success/40 text-base-content';
    case 'error':
      return 'bg-base-100/95 border-error/40 text-base-content';
    case 'warning':
      return 'bg-base-100/95 border-warning/40 text-base-content';
    default:
      return 'bg-base-100/95 border-info/40 text-base-content';
  }
}
</script>

