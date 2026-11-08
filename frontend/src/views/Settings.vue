<template>
  <div class="space-y-6 max-w-5xl mx-auto">
    <!-- Page Header -->
    <div class="flex items-center justify-between pb-2 border-b border-base-content/10">
      <div>
        <h1 class="text-xl sm:text-2xl font-bold">系统设置</h1>
        <p class="text-xs text-base-content/60">管理受管服务、运行清理策略、界面风格与安全选项</p>
      </div>
      <router-link to="/" class="btn btn-outline btn-sm">返回控制台</router-link>
    </div>

    <!-- Main Capsule Tabs Navigation (DaisyUI tabs-boxed) -->
    <div class="flex items-center overflow-x-auto pb-1">
      <div class="tabs tabs-boxed bg-base-200/90 p-1.5 rounded-2xl inline-flex gap-1 border border-base-content/10 shadow-sm max-w-full">
        <button 
          type="button" 
          :class="['tab tab-sm sm:tab-md rounded-xl font-medium transition-all gap-2', currentMainTab === 'services' ? 'tab-active bg-primary text-primary-content shadow-sm' : 'hover:bg-base-300/60']"
          @click="setMainTab('services')"
        >
          <ListChecks class="w-4 h-4" />
          <span>服务纳管</span>
          <span class="badge badge-xs" :class="currentMainTab === 'services' ? 'badge-neutral' : 'badge-primary'">{{ selectedUnits.length }}</span>
        </button>
        <button 
          type="button" 
          :class="['tab tab-sm sm:tab-md rounded-xl font-medium transition-all gap-2', currentMainTab === 'strategy' ? 'tab-active bg-primary text-primary-content shadow-sm' : 'hover:bg-base-300/60']"
          @click="setMainTab('strategy')"
        >
          <ShieldAlert class="w-4 h-4" />
          <span>运行策略</span>
        </button>
        <button 
          type="button" 
          :class="['tab tab-sm sm:tab-md rounded-xl font-medium transition-all gap-2', currentMainTab === 'appearance' ? 'tab-active bg-primary text-primary-content shadow-sm' : 'hover:bg-base-300/60']"
          @click="setMainTab('appearance')"
        >
          <Palette class="w-4 h-4" />
          <span>外观主题</span>
        </button>
        <button 
          type="button" 
          :class="['tab tab-sm sm:tab-md rounded-xl font-medium transition-all gap-2', currentMainTab === 'security' ? 'tab-active bg-primary text-primary-content shadow-sm' : 'hover:bg-base-300/60']"
          @click="setMainTab('security')"
        >
          <Lock class="w-4 h-4" />
          <span>账户安全</span>
        </button>
      </div>
    </div>

    <!-- Tab 1: Systemd Services Discovery & Selection (Core User Requirement) -->
    <div v-show="currentMainTab === 'services'" class="card bg-base-100 shadow border border-base-content/10">
      <div class="card-body p-4 sm:p-6 space-y-4">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h2 class="font-bold text-base flex items-center gap-2">
              <ListChecks class="w-5 h-5 text-primary" />
              <span>选择纳入 Web 管理的程序 (已勾选 {{ selectedUnits.length }} 个)</span>
            </h2>
            <p class="text-xs text-base-content/60">
              勾选后将呈现在控制台首页，首页仅能操作这些被勾选的程序。
            </p>
          </div>

          <div class="flex items-center gap-2">
            <button class="btn btn-primary btn-sm" :disabled="savingUnits" @click="saveSelectedUnits">
              <span v-if="savingUnits" class="loading loading-spinner loading-xs"></span>
              <Save v-else class="w-4 h-4" />
              <span>保存纳管清单</span>
            </button>
          </div>
        </div>

        <!-- Categorized Tabs & Quick Filters -->
        <div class="flex flex-wrap items-center justify-between gap-2 border-b border-base-content/10 pb-2">
          <div class="tabs tabs-boxed bg-base-200/80 p-1">
            <button 
              type="button"
              :class="['tab tab-xs sm:tab-sm transition-all', activeTab === 'recommended' ? 'tab-active font-semibold' : '']"
              @click="activeTab = 'recommended'"
            >
              <Sparkles class="w-3.5 h-3.5 mr-1 text-primary" />
              <span>自建/推荐 ({{ recommendedCount }})</span>
            </button>
            <button 
              type="button"
              :class="['tab tab-xs sm:tab-sm transition-all', activeTab === 'managed' ? 'tab-active font-semibold' : '']"
              @click="activeTab = 'managed'"
            >
              <CheckCircle2 class="w-3.5 h-3.5 mr-1 text-success" />
              <span>已纳管 ({{ selectedUnits.length }})</span>
            </button>
            <button 
              type="button"
              :class="['tab tab-xs sm:tab-sm transition-all', activeTab === 'all' ? 'tab-active font-semibold' : '']"
              @click="onSelectAllTab"
            >
              <Layers class="w-3.5 h-3.5 mr-1" />
              <span>全部系统服务</span>
            </button>
          </div>

          <button 
            type="button"
            :class="['btn btn-xs gap-1.5 transition-all', onlyActive ? 'btn-success text-white' : 'btn-outline border-base-content/20']"
            @click="onlyActive = !onlyActive"
          >
            <span class="w-2 h-2 rounded-full" :class="onlyActive ? 'bg-white' : 'bg-base-content/40'"></span>
            <span>仅看运行中 (Active)</span>
          </button>
        </div>

        <!-- Filter input -->
        <div class="form-control">
          <input 
            v-model="searchKeyword" 
            type="text" 
            placeholder="搜索程序名称 (如 ollama, comfyui, vllm, sd, whisper)..." 
            class="input input-bordered input-sm w-full"
          />
        </div>

        <!-- Candidate list table -->
        <div class="overflow-x-auto max-h-80 border border-base-content/10 rounded-lg">
          <table class="table table-xs sm:table-sm table-pin-rows">
            <thead>
              <tr class="bg-base-200">
                <th class="w-12 text-center">纳入</th>
                <th>服务标识 (Unit Name)</th>
                <th>显示别名 (备注)</th>
                <th>状态与来源</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="candidateLoading">
                <td colspan="4" class="text-center py-8">
                  <span class="loading loading-spinner loading-md"></span>
                </td>
              </tr>
              <tr v-else-if="filteredCandidates.length === 0">
                <td colspan="4" class="text-center py-8 text-base-content/50 text-xs">
                  暂无匹配的候选服务
                </td>
              </tr>
              <tr 
                v-else
                v-for="item in filteredCandidates" 
                :key="item.unit_name"
                class="hover:bg-base-200/50"
              >
                <td class="text-center">
                  <input 
                    type="checkbox" 
                    :checked="isUnitSelected(item.unit_name)"
                    @change="toggleUnit(item)"
                    class="checkbox checkbox-sm checkbox-primary" 
                  />
                </td>
                <td class="font-mono text-xs">
                  <span class="font-semibold">{{ item.unit_name }}</span>
                </td>
                <td>
                  <input 
                    type="text" 
                    :value="getUnitDisplayName(item.unit_name)"
                    @input="updateDisplayName(item.unit_name, ($event.target as HTMLInputElement).value)"
                    placeholder="输入自定义别名"
                    class="input input-bordered input-xs w-full max-w-xs"
                  />
                </td>
                <td>
                  <div class="flex items-center gap-1.5 flex-wrap">
                    <span 
                      v-if="item.source_type === 'custom'" 
                      class="badge badge-xs badge-success text-[10px]"
                    >自建服务</span>
                    <span 
                      v-else-if="item.source_type === 'user_scope' || item.scope === 'user'" 
                      class="badge badge-xs badge-info text-[10px]"
                    >用户级</span>
                    <span 
                      v-else 
                      class="badge badge-xs badge-ghost text-[10px]"
                    >系统预装</span>

                    <span 
                      :class="['badge badge-xs badge-outline text-[10px]', item.active_state === 'active' ? 'badge-success' : 'badge-ghost opacity-60']"
                    >
                      {{ item.active_state === 'active' ? '运行中' : '未运行' }}
                    </span>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Fallback: Add Custom Program Form -->
        <div class="collapse collapse-arrow bg-base-200/50 border border-base-content/10 text-xs">
          <input type="checkbox" /> 
          <div class="collapse-title font-semibold flex items-center gap-1.5 text-base-content/80">
            <PlusCircle class="w-4 h-4 text-secondary" />
            <span>未在列表中找到？点击手动添加自定义程序 (兜底方案)</span>
          </div>
          <div class="collapse-content space-y-3 pt-2">
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div class="form-control">
                <label class="label"><span class="label-text text-xs">显示名称</span></label>
                <input v-model="customForm.display_name" type="text" placeholder="例如: 本地大模型" class="input input-bordered input-xs" />
              </div>
              <div class="form-control">
                <label class="label"><span class="label-text text-xs">服务名/Identifier</span></label>
                <input v-model="customForm.unit_name" type="text" placeholder="例如: my-ai.service" class="input input-bordered input-xs" />
              </div>
            </div>
            <button class="btn btn-secondary btn-xs" @click="submitCustomUnit">添加到纳管列表</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Tab 2: Strategy Settings (Force Kill & Cleanup) -->
    <div v-show="currentMainTab === 'strategy'" class="card bg-base-100 shadow border border-base-content/10">
      <div class="card-body p-4 sm:p-6 space-y-4">
        <h2 class="font-bold text-base flex items-center gap-2">
          <ShieldAlert class="w-5 h-5 text-warning" />
          <span>控制策略与资源清理配置</span>
        </h2>

        <div class="space-y-3 text-sm">
          <!-- Force Kill Option -->
          <div class="flex items-center justify-between p-3 rounded-lg bg-base-200/40">
            <div>
              <div class="font-semibold text-xs sm:text-sm">超时强制终止 (Force Kill)</div>
              <p class="text-xs text-base-content/60">当服务停止超时未退出时，自动调用 systemctl kill 强制杀掉进程</p>
            </div>
            <input type="checkbox" v-model="settings.enable_force_kill" class="toggle toggle-sm toggle-warning" />
          </div>

          <!-- Ghost Cleaning Option -->
          <div class="flex items-center justify-between p-3 rounded-lg bg-base-200/40">
            <div>
              <div class="font-semibold text-xs sm:text-sm">多维资源清理 (显存 + 内存 + CPU)</div>
              <p class="text-xs text-base-content/60">在一键全停时自动扫描并清理残留的 GPU 显存进程、内存页缓存与孤儿任务</p>
            </div>
            <input type="checkbox" v-model="settings.enable_ghost_cleaning" class="toggle toggle-sm toggle-success" />
          </div>
        </div>

        <div class="flex justify-end">
          <button class="btn btn-warning btn-sm" @click="saveSettings">保存策略设置</button>
        </div>
      </div>
    </div>

    <!-- Tab 3: DaisyUI Theme Gallery (Rich UI Requirement) -->
    <div v-show="currentMainTab === 'appearance'" class="card bg-base-100 shadow border border-base-content/10">
      <div class="card-body p-4 sm:p-6 space-y-4">
        <div>
          <h2 class="font-bold text-base flex items-center gap-2">
            <Palette class="w-5 h-5 text-info" />
            <span>DaisyUI 丰富主题画廊 (当前: {{ themeStore.currentTheme }})</span>
          </h2>
          <p class="text-xs text-base-content/60">内置展示 DaisyUI 原生精美主题风格，点击即可一键自由切换</p>
        </div>

        <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-2.5">
          <button
            v-for="t in themeStore.themes"
            :key="t.id"
            :class="[
              'p-2.5 rounded-xl border text-left flex flex-col justify-between transition-all cursor-pointer',
              themeStore.currentTheme === t.id 
                ? 'border-primary ring-2 ring-primary/40 bg-base-200' 
                : 'border-base-content/10 hover:border-base-content/30 bg-base-200/40'
            ]"
            @click="themeStore.setTheme(t.id)"
          >
            <span class="text-xs font-semibold truncate">{{ t.name }}</span>
            <div class="flex items-center gap-1 mt-2">
              <span 
                v-for="(c, idx) in t.colors" 
                :key="idx" 
                class="w-3.5 h-3.5 rounded-full border border-black/20" 
                :style="{ backgroundColor: c }"
              ></span>
            </div>
          </button>
        </div>
      </div>
    </div>

    <!-- Tab 4: Security Password Change -->
    <div v-show="currentMainTab === 'security'" class="card bg-base-100 shadow border border-base-content/10">
      <div class="card-body p-4 sm:p-6 space-y-4">
        <h2 class="font-bold text-base flex items-center gap-2">
          <Lock class="w-5 h-5 text-accent" />
          <span>修改管理密码</span>
        </h2>
        
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-md">
          <div class="form-control">
            <label class="label"><span class="label-text text-xs">当前旧密码</span></label>
            <input v-model="pwdForm.old_pwd" type="password" class="input input-bordered input-sm" />
          </div>
          <div class="form-control">
            <label class="label"><span class="label-text text-xs">新密码 (至少6位)</span></label>
            <input v-model="pwdForm.new_pwd" type="password" class="input input-bordered input-sm" />
          </div>
        </div>

        <div class="flex items-center gap-3">
          <button class="btn btn-accent btn-sm" @click="changePassword">更新密码</button>
          <span v-if="pwdMsg" class="text-xs font-medium" :class="pwdSuccess ? 'text-success' : 'text-error'">
            {{ pwdMsg }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { 
  ListChecks, Save, PlusCircle, ShieldAlert, Palette, Lock, 
  Sparkles, CheckCircle2, Layers 
} from 'lucide-vue-next';
import api from '../api/client';
import { useThemeStore } from '../stores/theme';
import { useServicesStore } from '../stores/services';
import { useToastStore } from '../stores/toast';

const route = useRoute();
const router = useRouter();
const themeStore = useThemeStore();
const servicesStore = useServicesStore();
const toastStore = useToastStore();

type MainTab = 'services' | 'strategy' | 'appearance' | 'security';
const currentMainTab = ref<MainTab>('services');

function setMainTab(tab: MainTab) {
  currentMainTab.value = tab;
  router.replace({ query: { ...route.query, tab } });
}

const candidateLoading = ref(false);
const savingUnits = ref(false);
const includeCoreServices = ref(false);
const searchKeyword = ref('');
const candidates = ref<any[]>([]);
const selectedUnits = ref<any[]>([]);

const activeTab = ref<'recommended' | 'managed' | 'all'>('recommended');
const onlyActive = ref(false);

const recommendedCount = computed(() => {
  return candidates.value.filter((c) => c.is_recommended || c.source_type !== 'system_package').length;
});

async function onSelectAllTab() {
  activeTab.value = 'all';
  if (!includeCoreServices.value) {
    includeCoreServices.value = true;
    await loadCandidates();
  }
}

const settings = ref({
  enable_force_kill: true,
  kill_timeout_seconds: 8,
  enable_ghost_cleaning: true,
});

const customForm = ref({
  display_name: '',
  unit_name: '',
});

const pwdForm = ref({ old_pwd: '', new_pwd: '' });
const pwdMsg = ref('');
const pwdSuccess = ref(false);

const filteredCandidates = computed(() => {
  let list = candidates.value;

  // 1. Tab filter
  if (activeTab.value === 'recommended') {
    list = list.filter((c) => c.is_recommended || c.source_type !== 'system_package');
  } else if (activeTab.value === 'managed') {
    list = list.filter((c) => isUnitSelected(c.unit_name));
  }

  // 2. Active status filter
  if (onlyActive.value) {
    list = list.filter((c) => c.active_state === 'active');
  }

  // 3. Search keyword filter
  const kw = searchKeyword.value.toLowerCase().trim();
  if (kw) {
    list = list.filter(
      (c) => c.unit_name.toLowerCase().includes(kw) || (c.description && c.description.toLowerCase().includes(kw))
    );
  }

  return list;
});

async function loadCandidates() {
  candidateLoading.value = true;
  try {
    const res = await api.get('/systemd/candidates', {
      params: { include_core: includeCoreServices.value },
    });
    candidates.value = res.data;
  } finally {
    candidateLoading.value = false;
  }
}

async function loadConfig() {
  try {
    const res = await api.get('/systemd/config');
    selectedUnits.value = res.data.units || [];
    if (res.data.settings) {
      settings.value = { ...settings.value, ...res.data.settings };
    }
  } catch (e) {
    console.error(e);
  }
}

function isUnitSelected(unitName: string) {
  return selectedUnits.value.some((u) => u.unit_name === unitName);
}

function getUnitDisplayName(unitName: string) {
  const found = selectedUnits.value.find((u) => u.unit_name === unitName);
  return found ? found.display_name : '';
}

function updateDisplayName(unitName: string, name: string) {
  const found = selectedUnits.value.find((u) => u.unit_name === unitName);
  if (found) {
    found.display_name = name;
  }
}

function toggleUnit(item: any) {
  const index = selectedUnits.value.findIndex((u) => u.unit_name === item.unit_name);
  if (index >= 0) {
    selectedUnits.value.splice(index, 1);
  } else {
    // Generate intelligent default display name
    const prettyName = item.unit_name
      .replace('.service', '')
      .split('-')
      .map((w: string) => w.charAt(0).toUpperCase() + w.slice(1))
      .join(' ');
    selectedUnits.value.push({
      unit_name: item.unit_name,
      display_name: prettyName,
      scope: item.scope || 'system',
      enabled: true,
    });
  }
}

async function saveSelectedUnits() {
  savingUnits.value = true;
  try {
    await api.post('/systemd/config/units', { units: selectedUnits.value });
    await servicesStore.refreshAll();
    toastStore.success('纳管服务配置已成功保存！首页控制台已同步更新。');
  } finally {
    savingUnits.value = false;
  }
}

async function submitCustomUnit() {
  if (!customForm.value.display_name || !customForm.value.unit_name) {
    toastStore.warning('请完整填写显示名称与服务名');
    return;
  }
  await api.post('/systemd/config/custom', {
    display_name: customForm.value.display_name,
    unit_name: customForm.value.unit_name,
  });
  customForm.value = { display_name: '', unit_name: '' };
  await loadConfig();
  await loadCandidates();
  toastStore.success('自定义程序已成功添加！');
}

async function saveSettings() {
  await api.post('/systemd/config/settings', settings.value);
  toastStore.success('控制策略设置已更新');
}

async function changePassword() {
  pwdMsg.value = '';
  try {
    await api.post('/auth/password', {
      old_password: pwdForm.value.old_pwd,
      new_password: pwdForm.value.new_pwd,
    });
    pwdSuccess.value = true;
    pwdMsg.value = '密码修改成功，请妥善保存！';
    pwdForm.value = { old_pwd: '', new_pwd: '' };
  } catch (e: any) {
    pwdSuccess.value = false;
    pwdMsg.value = e.response?.data?.detail || '密码修改失败';
  }
}

onMounted(async () => {
  const queryTab = route.query.tab as string;
  if (queryTab && ['services', 'strategy', 'appearance', 'security'].includes(queryTab)) {
    currentMainTab.value = queryTab as MainTab;
  }
  await loadConfig();
  await loadCandidates();
});
</script>
