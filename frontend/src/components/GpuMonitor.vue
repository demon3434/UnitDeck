<template>
  <div v-if="gpu" class="card bg-base-100 shadow-md border border-base-content/10">
    <div class="card-body p-4 sm:p-5">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3">
        <div class="flex items-center gap-2">
          <div class="p-2 rounded-lg bg-primary/10 text-primary">
            <Cpu class="w-5 h-5" />
          </div>
          <div>
            <h2 class="text-sm sm:text-base font-bold flex items-center gap-2">
              {{ gpu.name || 'NVIDIA GPU' }}
              <span class="badge badge-sm badge-outline font-mono text-xs">
                {{ (gpu.total_memory_mb / 1024).toFixed(1) }} GB 显存
              </span>
            </h2>
            <p class="text-xs text-base-content/60">
              驱动: {{ gpu.driver_version }} | CUDA: {{ gpu.cuda_version }}
            </p>
          </div>
        </div>

        <div class="flex items-center gap-4 text-xs font-mono self-end sm:self-center">
          <div class="flex items-center gap-1.5" title="GPU核心利用率">
            <Activity class="w-3.5 h-3.5 text-info" />
            <span>负载: {{ gpu.gpu_utilization_percent }}%</span>
          </div>
          <div class="flex items-center gap-1.5" title="核心温度">
            <Thermometer class="w-3.5 h-3.5" :class="gpu.temperature_celsius > 75 ? 'text-error' : 'text-success'" />
            <span>{{ gpu.temperature_celsius }}°C</span>
          </div>
          <div v-if="gpu.power_watts" class="flex items-center gap-1.5 hidden md:flex" title="功耗">
            <Zap class="w-3.5 h-3.5 text-warning" />
            <span>{{ gpu.power_watts }}W</span>
          </div>
        </div>
      </div>

      <!-- VRAM Progress Bar -->
      <div class="space-y-1.5">
        <div class="flex justify-between items-center text-xs">
          <span class="font-medium flex items-center gap-1">
            显存占用 (VRAM)
            <span :class="['font-mono font-bold', getPercentTextColor(gpu.memory_percent)]">
              {{ gpu.memory_percent }}%
            </span>
          </span>
          <span class="font-mono text-base-content/70">
            <span class="text-base-content font-semibold">{{ (gpu.used_memory_mb / 1024).toFixed(2) }} GB</span>
            / {{ (gpu.total_memory_mb / 1024).toFixed(1) }} GB
            <span class="badge badge-xs badge-neutral ml-2">余 {{ (gpu.free_memory_mb / 1024).toFixed(2) }} GB</span>
          </span>
        </div>

        <progress 
          class="progress w-full h-3 transition-all duration-300"
          :class="getProgressColor(gpu.memory_percent)"
          :value="gpu.used_memory_mb" 
          :max="gpu.total_memory_mb"
        ></progress>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Cpu, Activity, Thermometer, Zap } from 'lucide-vue-next';
import type { GpuStatus } from '../stores/services';

defineProps<{
  gpu: GpuStatus | null;
}>();

function getProgressColor(percent: number) {
  if (percent >= 85) return 'progress-error';
  if (percent >= 65) return 'progress-warning';
  return 'progress-primary';
}

function getPercentTextColor(percent: number) {
  if (percent >= 85) return 'text-error';
  if (percent >= 65) return 'text-warning';
  return 'text-primary';
}
</script>

