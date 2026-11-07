<template>
  <div class="space-y-3">
    <!-- Title & Status Header -->
    <div class="flex items-center justify-between pb-2 border-b border-base-content/10">
      <div class="flex items-center gap-1.5 font-bold text-xs">
        <Activity class="w-3.5 h-3.5 text-primary animate-pulse" />
        <span>系统硬件实时监控</span>
      </div>
      <div class="flex items-center gap-1 text-[11px] text-success font-medium">
        <span class="w-2 h-2 rounded-full bg-success"></span>
        <span>正常运行</span>
      </div>
    </div>

    <!-- Section 1: CPU & RAM -->
    <div class="bg-base-200/50 p-3 rounded-xl border border-base-content/5 space-y-2.5">
      <!-- Header -->
      <div class="flex items-center justify-between">
        <span class="font-bold text-xs flex items-center gap-1.5">
          <Cpu class="w-3.5 h-3.5 text-primary" />
          <span>主机计算与内存 (CPU & RAM)</span>
        </span>
        <span v-if="metrics?.cpu?.temperature_celsius" class="badge badge-xs badge-outline badge-primary font-mono text-[10px]">
          CPU {{ metrics.cpu.temperature_celsius }}°C
        </span>
      </div>

      <!-- CPU Metric -->
      <div class="space-y-0.5">
        <div class="flex items-center justify-between text-[11px]">
          <span class="text-base-content/70">CPU 使用率</span>
          <span class="font-mono font-bold text-primary">
            {{ metrics ? metrics.cpu.percent.toFixed(1) : '--' }}%
          </span>
        </div>
        <progress 
          class="progress progress-primary w-full h-1.5 rounded-full" 
          :value="metrics?.cpu?.percent || 0" 
          max="100"
        ></progress>
      </div>

      <!-- RAM Metric -->
      <div class="space-y-0.5">
        <div class="flex items-center justify-between text-[11px]">
          <span class="text-base-content/70">物理内存 (RAM)</span>
          <span class="font-mono font-bold text-info">
            {{ formatGb(metrics?.ram?.used_mb) }} / {{ formatGb(metrics?.ram?.total_mb) }} ({{ metrics ? metrics.ram.percent.toFixed(1) : '--' }}%)
          </span>
        </div>
        <progress 
          class="progress progress-info w-full h-1.5 rounded-full" 
          :value="metrics?.ram?.percent || 0" 
          max="100"
        ></progress>
      </div>

      <!-- CPU Detail -->
      <div class="flex items-center justify-between text-[10px] text-base-content/60 pt-1 border-t border-base-content/5">
        <span class="truncate max-w-[170px]" :title="metrics?.cpu?.model">
          {{ metrics?.cpu?.model ? metrics.cpu.model.split('@')[0] : 'CPU' }} ({{ metrics ? metrics.cpu.cores : '--' }} 核)
        </span>
        <span>余 {{ formatGb(metrics?.ram?.free_mb) }}</span>
      </div>
    </div>

    <!-- Section 2: GPU & VRAM -->
    <div class="bg-base-200/50 p-3 rounded-xl border border-base-content/5 space-y-2.5">
      <!-- Header -->
      <div class="flex items-center justify-between">
        <span class="font-bold text-xs flex items-center gap-1.5">
          <Zap class="w-3.5 h-3.5 text-warning" />
          <span>显卡算力与显存 (GPU & VRAM)</span>
        </span>
        <span class="badge badge-xs badge-outline badge-warning font-mono text-[10px]">
          GPU {{ metrics?.gpu?.temperature_celsius ? metrics.gpu.temperature_celsius + '°C' : '--°C' }}
        </span>
      </div>

      <!-- GPU Load Metric -->
      <div class="space-y-0.5">
        <div class="flex items-center justify-between text-[11px]">
          <span class="text-base-content/70">GPU 核心负载</span>
          <span class="font-mono font-bold text-warning">
            {{ metrics?.gpu ? metrics.gpu.gpu_utilization_percent : 0 }}%
          </span>
        </div>
        <progress 
          class="progress progress-warning w-full h-1.5 rounded-full" 
          :value="metrics?.gpu?.gpu_utilization_percent || 0" 
          max="100"
        ></progress>
      </div>

      <!-- VRAM Metric -->
      <div class="space-y-0.5">
        <div class="flex items-center justify-between text-[11px]">
          <span class="text-base-content/70">显存占用 (VRAM)</span>
          <span class="font-mono font-bold text-accent">
            {{ formatGb(metrics?.gpu?.used_memory_mb) }} / {{ formatGb(metrics?.gpu?.total_memory_mb) }} ({{ metrics?.gpu ? metrics.gpu.memory_percent.toFixed(1) : 0 }}%)
          </span>
        </div>
        <progress 
          class="progress progress-accent w-full h-1.5 rounded-full" 
          :value="metrics?.gpu?.memory_percent || 0" 
          max="100"
        ></progress>
      </div>

      <!-- GPU Detail -->
      <div class="flex items-center justify-between text-[10px] text-base-content/60 pt-1 border-t border-base-content/5">
        <span class="truncate max-w-[170px]" :title="metrics?.gpu?.name">
          {{ metrics?.gpu?.name || 'AMD Radeon GPU' }}
        </span>
        <span>{{ metrics?.gpu?.cuda_version || 'ROCm/Sysfs' }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Cpu, Zap, Activity } from 'lucide-vue-next';
import type { SystemMetrics } from '../stores/services';

defineProps<{
  metrics: SystemMetrics | null;
}>();

function formatGb(mb?: number): string {
  if (mb === undefined || mb === null) return '-- GB';
  return `${(mb / 1024).toFixed(1)} GB`;
}
</script>
