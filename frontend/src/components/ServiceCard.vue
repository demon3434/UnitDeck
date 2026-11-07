<template>
  <div 
    class="card bg-base-100 shadow hover:shadow-md transition-all duration-200 border"
    :class="cardBorderClass"
  >
    <div class="card-body p-4 sm:p-5">
      <!-- Header: Title & Badges -->
      <div class="flex items-start justify-between gap-2">
        <div class="space-y-1 flex-1 min-w-0">
          <div class="flex items-center gap-2 flex-wrap">
            <h3 class="font-bold text-base sm:text-lg truncate" :title="service.display_name">
              {{ service.display_name }}
            </h3>
            <span class="badge badge-sm badge-neutral text-xs">
              {{ service.category || 'AI' }}
            </span>
            <span v-if="service.scope === 'user'" class="badge badge-sm badge-ghost text-xs">
              用户级
            </span>
          </div>
          <p class="font-mono text-xs text-base-content/60 truncate" :title="service.unit_name">
            {{ service.unit_name }}
          </p>
        </div>

        <!-- Status Pill -->
        <div :class="['badge badge-md gap-1.5 font-medium shrink-0', statusBadgeClass]">
          <span :class="['w-2 h-2 rounded-full', statusDotClass]"></span>
          {{ statusLabel }}
        </div>
      </div>

      <!-- Description if any -->
      <p v-if="service.description" class="text-xs text-base-content/70 line-clamp-1 my-1">
        {{ service.description }}
      </p>

      <!-- Runtime Stats: Memory, PID, Boot auto-start toggle -->
      <div class="flex items-center justify-between text-xs py-2 my-1 border-y border-base-content/5 text-base-content/70">
        <div class="flex items-center gap-3 font-mono">
          <span v-if="service.status.memory_current">
            内存: <strong class="text-base-content">{{ service.status.memory_current }}</strong>
          </span>
          <span v-if="service.status.main_pid > 0">
            PID: <strong class="text-base-content">{{ service.status.main_pid }}</strong>
          </span>
          <span v-if="!service.status.memory_current && service.status.main_pid === 0">
            未占用系统资源
          </span>
        </div>

        <!-- Boot Auto-start Toggle (User requirement: switchable with confirm) -->
        <button 
          class="flex items-center gap-1.5 hover:text-base-content transition-colors cursor-pointer text-xs"
          @click="$emit('toggle-boot', service)"
          :title="service.status.is_enabled ? '点击关闭开机自启动' : '点击开启开机自启动'"
        >
          <span class="text-[11px]">开机自启:</span>
          <span 
            :class="['badge badge-xs font-mono', service.status.is_enabled ? 'badge-success text-success-content' : 'badge-ghost text-base-content/40']"
          >
            {{ service.status.is_enabled ? '已启用' : '已关闭' }}
          </span>
        </button>
      </div>

      <!-- Footer Action Buttons (All trigger confirm modal) -->
      <div class="card-actions justify-between items-center mt-2">
        <button 
          class="btn btn-ghost btn-xs gap-1 text-base-content/60 hover:text-base-content"
          @click="$emit('view-log', service)"
        >
          <FileText class="w-3.5 h-3.5" />
          <span>日志</span>
        </button>

        <div class="flex items-center gap-1.5">
          <!-- When active: Show Restart & Stop -->
          <template v-if="isActive">
            <button 
              class="btn btn-warning btn-outline btn-xs gap-1"
              :disabled="actionLoading"
              @click="$emit('action', service, 'restart')"
            >
              <RotateCw class="w-3 h-3" />
              <span>重启</span>
            </button>

            <button 
              class="btn btn-error btn-xs gap-1"
              :disabled="actionLoading"
              @click="$emit('action', service, 'stop')"
            >
              <Power class="w-3 h-3" />
              <span>停止</span>
            </button>
          </template>

          <!-- When inactive: Show Start -->
          <template v-else>
            <button 
              class="btn btn-success btn-xs gap-1 px-3"
              :disabled="actionLoading"
              @click="$emit('action', service, 'start')"
            >
              <Play class="w-3 h-3" />
              <span>启动</span>
            </button>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { Play, Power, RotateCw, FileText } from 'lucide-vue-next';
import type { ManagedService } from '../stores/services';

const props = defineProps<{
  service: ManagedService;
  actionLoading?: boolean;
}>();

defineEmits<{
  (e: 'action', service: ManagedService, action: 'start' | 'stop' | 'restart'): void;
  (e: 'toggle-boot', service: ManagedService): void;
  (e: 'view-log', service: ManagedService): void;
}>();

const isActive = computed(() => {
  return props.service.status.active_state === 'active' || props.service.status.active_state === 'activating';
});

const statusLabel = computed(() => {
  switch (props.service.status.active_state) {
    case 'active':
      return '运行中';
    case 'activating':
      return '启动中';
    case 'deactivating':
      return '停止中';
    case 'failed':
      return '异常退出';
    case 'inactive':
    default:
      return '已停止';
  }
});

const statusBadgeClass = computed(() => {
  switch (props.service.status.active_state) {
    case 'active':
      return 'badge-success text-success-content';
    case 'activating':
      return 'badge-info text-info-content';
    case 'failed':
      return 'badge-error text-error-content';
    case 'deactivating':
      return 'badge-warning text-warning-content';
    default:
      return 'badge-ghost text-base-content/60';
  }
});

const statusDotClass = computed(() => {
  switch (props.service.status.active_state) {
    case 'active':
      return 'bg-success animate-pulse';
    case 'failed':
      return 'bg-error';
    case 'activating':
    case 'deactivating':
      return 'bg-warning animate-spin';
    default:
      return 'bg-base-content/30';
  }
});

const cardBorderClass = computed(() => {
  if (isActive.value) {
    return 'border-success/30 bg-success/5';
  }
  if (props.service.status.active_state === 'failed') {
    return 'border-error/40 bg-error/5';
  }
  return 'border-base-content/10';
});
</script>

