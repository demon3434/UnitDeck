<template>
  <div class="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-base-100 p-3 sm:p-4 rounded-xl shadow-sm border border-base-content/10">
    <!-- Status stats -->
    <div class="flex items-center gap-3">
      <div class="badge badge-lg gap-2 font-mono">
        <span class="w-2.5 h-2.5 rounded-full bg-success animate-pulse"></span>
        运行中: <span class="font-bold text-success">{{ activeCount }}</span> / {{ totalCount }}
      </div>
      <span class="text-xs text-base-content/60 hidden sm:inline">
        共纳入 {{ totalCount }} 个程序管控
      </span>
    </div>

    <!-- Quick action buttons -->
    <div class="flex items-center gap-2 justify-end">
      <!-- Deep clean button -->
      <button 
        class="btn btn-outline btn-warning btn-sm gap-1.5 flex-1 sm:flex-initial"
        @click="$emit('trigger-clean')"
        title="清理脱离服务的显存、内存与CPU孤儿进程"
      >
        <Sparkles class="w-4 h-4" />
        <span>深度清理</span>
      </button>

      <!-- Stop all button (Primary user requirement) -->
      <button 
        class="btn btn-error btn-sm gap-1.5 flex-1 sm:flex-initial shadow-md"
        :disabled="activeCount === 0 || isStoppingAll"
        @click="$emit('trigger-stop-all')"
      >
        <span v-if="isStoppingAll" class="loading loading-spinner loading-xs"></span>
        <PowerOff v-else class="w-4 h-4" />
        <span class="font-bold">一键全停</span>
      </button>

      <!-- Refresh button -->
      <button 
        class="btn btn-ghost btn-circle btn-sm"
        :class="{ 'animate-spin': loading }"
        @click="$emit('refresh')"
        title="刷新状态"
      >
        <RotateCw class="w-4 h-4" />
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { PowerOff, Sparkles, RotateCw } from 'lucide-vue-next';

defineProps<{
  totalCount: number;
  activeCount: number;
  loading: boolean;
  isStoppingAll: boolean;
}>();

defineEmits<{
  (e: 'trigger-stop-all'): void;
  (e: 'trigger-clean'): void;
  (e: 'refresh'): void;
}>();
</script>

