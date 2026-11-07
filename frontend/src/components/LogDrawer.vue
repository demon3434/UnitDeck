<template>
  <div v-if="isOpen" class="fixed inset-0 z-50 flex justify-end bg-black/50 backdrop-blur-sm transition-opacity">
    <div class="bg-base-100 w-full max-w-2xl h-full shadow-2xl flex flex-col border-l border-base-content/10">
      <!-- Header -->
      <div class="p-4 border-b border-base-content/10 flex items-center justify-between bg-base-200/50">
        <div class="flex items-center gap-2">
          <Terminal class="w-5 h-5 text-primary" />
          <div>
            <h3 class="font-bold text-sm sm:text-base font-mono">{{ unitName }}</h3>
            <p class="text-xs text-base-content/60">journalctl 运行日志 (最近 {{ lineCount }} 行)</p>
          </div>
        </div>

        <div class="flex items-center gap-2">
          <button 
            class="btn btn-ghost btn-xs btn-circle"
            :class="{ 'animate-spin': loading }"
            @click="fetchLogs"
            title="刷新日志"
          >
            <RotateCw class="w-4 h-4" />
          </button>
          <button class="btn btn-ghost btn-xs btn-circle" @click="$emit('close')">
            <X class="w-4 h-4" />
          </button>
        </div>
      </div>

      <!-- Controls -->
      <div class="px-4 py-2 bg-base-200/30 flex items-center justify-between text-xs border-b border-base-content/5">
        <div class="flex items-center gap-2">
          <span>行数:</span>
          <select v-model="lineCount" @change="fetchLogs" class="select select-bordered select-xs">
            <option :value="50">50 行</option>
            <option :value="100">100 行</option>
            <option :value="200">200 行</option>
          </select>
        </div>
        <button class="btn btn-ghost btn-xs" @click="copyLogs">
          <Copy class="w-3 h-3 mr-1" />
          <span>{{ copied ? '已复制' : '复制' }}</span>
        </button>
      </div>

      <!-- Log Content -->
      <div class="flex-1 p-4 overflow-auto bg-neutral text-neutral-content font-mono text-xs leading-relaxed">
        <div v-if="loading" class="flex justify-center items-center h-32">
          <span class="loading loading-spinner loading-md"></span>
        </div>
        <pre v-else class="whitespace-pre-wrap break-all">{{ logContent || '暂无日志输出' }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { Terminal, RotateCw, X, Copy } from 'lucide-vue-next';
import api from '../api/client';

const props = defineProps<{
  isOpen: boolean;
  unitName: string;
  scope?: string;
}>();

defineEmits<{
  (e: 'close'): void;
}>();

const lineCount = ref(60);
const logContent = ref('');
const loading = ref(false);
const copied = ref(false);

async function fetchLogs() {
  if (!props.unitName) return;
  loading.value = true;
  try {
    const res = await api.get(`/logs/${props.unitName}`, {
      params: { lines: lineCount.value, scope: props.scope || 'system' },
    });
    logContent.value = res.data.content;
  } catch (e: any) {
    logContent.value = `获取日志失败: ${e.response?.data?.detail || e.message}`;
  } finally {
    loading.value = false;
  }
}

function copyLogs() {
  navigator.clipboard.writeText(logContent.value);
  copied.value = true;
  setTimeout(() => (copied.value = false), 2000);
}

watch(
  () => props.isOpen,
  (open) => {
    if (open) fetchLogs();
  }
);
</script>

