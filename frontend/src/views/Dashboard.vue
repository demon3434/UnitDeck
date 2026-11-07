<template>
  <div class="space-y-4 sm:space-y-5">
    <!-- Active Filter Indicator Bar (when navbar search keyword is active) -->
    <div 
      v-if="servicesStore.searchKeyword" 
      class="flex items-center justify-between px-3.5 py-2 bg-base-100 rounded-xl border border-primary/20 shadow-xs text-xs text-base-content/80"
    >
      <div class="flex items-center gap-2">
        <span class="badge badge-primary badge-sm font-medium">搜索筛选</span>
        <span>关键词：「<strong class="text-primary">{{ servicesStore.searchKeyword }}</strong>」</span>
        <span class="text-base-content/50">（共匹配 {{ filteredServices.length }} / {{ servicesStore.services.length }} 个程序）</span>
      </div>
      <button 
        type="button" 
        class="btn btn-ghost btn-xs text-base-content/60 hover:text-error"
        @click="servicesStore.searchKeyword = ''"
      >
        清空筛选 (Esc)
      </button>
    </div>

    <!-- Action Toolbar: Stop All, Clean, Refresh -->
    <QuickActions
      :total-count="servicesStore.services.length"
      :active-count="activeCount"
      :loading="servicesStore.loading"
      :is-stopping-all="servicesStore.isStoppingAll"
      @trigger-stop-all="promptStopAll"
      @trigger-clean="promptClean"
      @refresh="servicesStore.refreshAll"
    />

    <!-- Empty State: No Managed Services Configured -->
    <div 
      v-if="servicesStore.services.length === 0" 
      class="card bg-base-100 shadow p-8 text-center border border-dashed border-base-content/20"
    >
      <div class="max-w-md mx-auto space-y-3">
        <SlidersHorizontal class="w-10 h-10 mx-auto text-primary/60" />
        <h3 class="font-bold text-lg">尚未纳入任何程序</h3>
        <p class="text-xs text-base-content/60">
          请先前往“设置与纳管”页面，系统将自动扫描宿主机上的 systemd 软件，您可以自主勾选想要在本页面控制的程序。
        </p>
        <router-link to="/settings" class="btn btn-primary btn-sm mt-2">
          前往纳管配置
        </router-link>
      </div>
    </div>

    <!-- Search No Match State -->
    <div 
      v-else-if="filteredServices.length === 0"
      class="card bg-base-100 shadow p-8 text-center border border-base-content/10"
    >
      <div class="max-w-md mx-auto space-y-2">
        <p class="text-sm font-semibold">未找到与「{{ servicesStore.searchKeyword }}」匹配的纳管服务</p>
        <p class="text-xs text-base-content/60">可尝试更换搜索词，或清空搜索条件以查看全部程序。</p>
        <button class="btn btn-outline btn-xs mt-2" @click="servicesStore.searchKeyword = ''">
          清空搜索条件 (Esc)
        </button>
      </div>
    </div>

    <!-- Managed Services Cards Grid -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <ServiceCard
        v-for="service in filteredServices"
        :key="service.unit_name"
        :service="service"
        :action-loading="servicesStore.actionLoading[service.unit_name]"
        @action="promptAction"
        @toggle-boot="promptToggleBoot"
        @view-log="openLogDrawer"
      />
    </div>

    <!-- High-precaution Confirmation Modal (Mandatory User Requirement) -->
    <ConfirmModal
      :is-open="confirmModal.isOpen"
      :title="confirmModal.title"
      :message="confirmModal.message"
      :target-name="confirmModal.targetName"
      :action-type="confirmModal.actionType"
      :confirm-text="confirmModal.confirmText"
      :loading="confirmModal.loading"
      @confirm="executeConfirmedAction"
      @cancel="confirmModal.isOpen = false"
    />

    <!-- Systemd Journalctl Log Drawer -->
    <LogDrawer
      :is-open="logDrawer.isOpen"
      :unit-name="logDrawer.unitName"
      :scope="logDrawer.scope"
      @close="logDrawer.isOpen = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { SlidersHorizontal } from 'lucide-vue-next';
import { useServicesStore, type ManagedService } from '../stores/services';
import QuickActions from '../components/QuickActions.vue';
import ServiceCard from '../components/ServiceCard.vue';
import ConfirmModal from '../components/ConfirmModal.vue';
import LogDrawer from '../components/LogDrawer.vue';

const servicesStore = useServicesStore();

const filteredServices = computed(() => {
  const kw = servicesStore.searchKeyword.toLowerCase().trim();
  if (!kw) return servicesStore.services;
  return servicesStore.services.filter(
    (s) =>
      s.unit_name.toLowerCase().includes(kw) ||
      (s.display_name && s.display_name.toLowerCase().includes(kw)) ||
      (s.description && s.description.toLowerCase().includes(kw)) ||
      (s.category && s.category.toLowerCase().includes(kw))
  );
});

const activeCount = computed(() => {
  return servicesStore.services.filter(
    (s) => s.status.active_state === 'active' || s.status.active_state === 'activating'
  ).length;
});

// Confirmation Modal State
const confirmModal = ref({
  isOpen: false,
  title: '',
  message: '',
  targetName: '',
  actionType: 'start' as any,
  confirmText: '确定',
  loading: false,
  actionFn: async () => {},
});

// Log Drawer State
const logDrawer = ref({
  isOpen: false,
  unitName: '',
  scope: 'system',
});

function openLogDrawer(service: ManagedService) {
  logDrawer.value = {
    isOpen: true,
    unitName: service.unit_name,
    scope: service.scope,
  };
}

function promptAction(service: ManagedService, action: 'start' | 'stop' | 'restart') {
  const actionText = action === 'start' ? '启动' : action === 'stop' ? '停止' : '重启';
  confirmModal.value = {
    isOpen: true,
    title: `确认${actionText}服务`,
    message: `您确定要对服务执行【${actionText}】操作吗？`,
    targetName: `${service.display_name} (${service.unit_name})`,
    actionType: action,
    confirmText: `立即${actionText}`,
    loading: false,
    actionFn: async () => {
      await servicesStore.executeAction(service.unit_name, action, service.scope);
    },
  };
}

function promptToggleBoot(service: ManagedService) {
  const willEnable = !service.status.is_enabled;
  const action = willEnable ? 'enable' : 'disable';
  const actionText = willEnable ? '开启开机自启' : '关闭开机自启';
  confirmModal.value = {
    isOpen: true,
    title: `确认${actionText}`,
    message: `操作后该服务在 Debian 宿主机开机时将${willEnable ? '自动启动' : '不会自动运行'}。`,
    targetName: `${service.display_name} (${service.unit_name})`,
    actionType: willEnable ? 'enable' : 'disable',
    confirmText: `确认${actionText}`,
    loading: false,
    actionFn: async () => {
      await servicesStore.executeAction(service.unit_name, action, service.scope);
    },
  };
}

function promptStopAll() {
  confirmModal.value = {
    isOpen: true,
    title: '⚠️ 确认一键全部停止运行',
    message: '此操作将立即停止所有纳管的运行中 AI 服务，以瞬间腾空 12GB 显存供其它程序使用。\n是否确定执行？',
    targetName: `将停止 ${activeCount.value} 个运行中的服务`,
    actionType: 'stop-all',
    confirmText: '确认全部停止',
    loading: false,
    actionFn: async () => {
      await servicesStore.stopAll();
    },
  };
}

function promptClean() {
  confirmModal.value = {
    isOpen: true,
    title: '确认深度清理资源',
    message: '系统将扫描并终结脱离服务的孤儿/残留 GPU 显存进程，并同步刷新内存与CPU缓存。',
    targetName: '显存 (VRAM) + 内存 (RAM) + CPU 深度释放',
    actionType: 'clean',
    confirmText: '立即深度清理',
    loading: false,
    actionFn: async () => {
      await servicesStore.deepClean();
    },
  };
}

async function executeConfirmedAction() {
  confirmModal.value.loading = true;
  try {
    await confirmModal.value.actionFn();
    confirmModal.value.isOpen = false;
  } finally {
    confirmModal.value.loading = false;
  }
}

onMounted(() => {
  servicesStore.startPolling(3500);
});

onUnmounted(() => {
  servicesStore.stopPolling();
});
</script>

