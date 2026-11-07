import { defineStore } from 'pinia';
import { ref } from 'vue';
import api from '../api/client';

export interface UnitDetail {
  unit_name: string;
  scope: string;
  load_state: string;
  active_state: string; // active, inactive, failed, etc.
  sub_state: string;
  is_enabled: boolean;
  main_pid: number;
  memory_current: string | null;
  started_at: string | null;
  description: string;
}

export interface ManagedService {
  unit_name: string;
  display_name: string;
  description: string;
  category: string;
  scope: string;
  is_custom: boolean;
  status: UnitDetail;
}

export interface GpuStatus {
  available: boolean;
  name: string;
  driver_version: string;
  cuda_version: string;
  total_memory_mb: number;
  used_memory_mb: number;
  free_memory_mb: number;
  memory_percent: number;
  gpu_utilization_percent: number;
  temperature_celsius: number;
  power_watts?: number;
}

export interface SystemMetrics {
  cpu: {
    percent: number;
    cores: number;
    model: string;
    load_avg: number[];
    temperature_celsius?: number;
  };
  ram: {
    total_mb: number;
    used_mb: number;
    free_mb: number;
    percent: number;
  };
  disk: {
    path: string;
    total_gb: number;
    used_gb: number;
    free_gb: number;
    percent: number;
  };
  net: {
    rx_kb_s: number;
    tx_kb_s: number;
    total_rx_gb: number;
    total_tx_gb: number;
  };
  gpu: GpuStatus;
}

export const useServicesStore = defineStore('services', () => {
  const services = ref<ManagedService[]>([]);
  const gpu = ref<GpuStatus | null>(null);
  const metrics = ref<SystemMetrics | null>(null);
  const searchKeyword = ref('');
  const loading = ref(false);
  const actionLoading = ref<Record<string, boolean>>({});
  const isStoppingAll = ref(false);
  let pollTimer: any = null;

  async function fetchServices() {
    try {
      const res = await api.get('/services/status');
      services.value = res.data;
    } catch (e) {
      console.error('Fetch services failed', e);
    }
  }

  async function fetchMetrics() {
    try {
      const res = await api.get('/system/metrics');
      metrics.value = res.data;
      if (res.data.gpu) {
        gpu.value = res.data.gpu;
      }
    } catch (e) {
      console.error('Fetch metrics failed', e);
    }
  }

  async function refreshAll() {
    loading.value = true;
    await Promise.all([fetchServices(), fetchMetrics()]);
    loading.value = false;
  }

  async function executeAction(unitName: string, action: string, scope = 'system') {
    actionLoading.value[unitName] = true;
    try {
      await api.post('/services/action', {
        unit_name: unitName,
        action,
        scope,
      });
      await refreshAll();
      return { success: true };
    } catch (e: any) {
      return { success: false, error: e.response?.data?.detail || e.message };
    } finally {
      actionLoading.value[unitName] = false;
    }
  }

  async function stopAll() {
    isStoppingAll.value = true;
    try {
      const res = await api.post('/services/stop-all');
      await refreshAll();
      return { success: true, data: res.data };
    } catch (e: any) {
      return { success: false, error: e.response?.data?.detail || e.message };
    } finally {
      isStoppingAll.value = false;
    }
  }

  async function deepClean() {
    try {
      const res = await api.post('/services/clean');
      await refreshAll();
      return { success: true, data: res.data };
    } catch (e: any) {
      return { success: false, error: e.response?.data?.detail || e.message };
    }
  }

  function startPolling(intervalMs = 4000) {
    stopPolling();
    refreshAll();
    pollTimer = setInterval(refreshAll, intervalMs);
  }

  function stopPolling() {
    if (pollTimer) {
      clearInterval(pollTimer);
      pollTimer = null;
    }
  }

  return {
    services,
    gpu,
    metrics,
    searchKeyword,
    loading,
    actionLoading,
    isStoppingAll,
    fetchServices,
    fetchGpu: fetchMetrics,
    fetchMetrics,
    refreshAll,
    executeAction,
    stopAll,
    deepClean,
    startPolling,
    stopPolling,
  };
});

