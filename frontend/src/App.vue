<template>
  <div class="min-h-screen flex flex-col bg-base-300 text-base-content antialiased">
    <!-- Top Navbar (Only when logged in) -->
    <header v-if="authStore.isAuthenticated" class="navbar bg-base-100 shadow-sm border-b border-base-content/10 px-3 sm:px-6 md:px-8 gap-2">
      <!-- Left: Logo & Brand -->
      <div class="flex items-center gap-2 shrink-0">
        <router-link to="/" class="flex items-center gap-2.5 font-black text-lg tracking-tight hover:opacity-80">
          <div class="p-1.5 rounded-lg bg-primary text-primary-content">
            <Cpu class="w-5 h-5" />
          </div>
          <span class="hidden sm:inline">UnitDeck</span>
          <span class="badge badge-xs badge-primary font-mono hidden md:inline">v1.0</span>
        </router-link>
      </div>

      <!-- Center: GitHub-Style Global Search in Navbar -->
      <div class="flex-1 max-w-xs sm:max-w-sm md:max-w-md lg:max-w-lg mx-auto px-1 sm:px-2">
        <label class="input input-sm flex items-center gap-2 bg-base-200/70 border border-base-content/15 rounded-xl hover:border-base-content/30 focus-within:border-primary focus-within:ring-2 focus-within:ring-primary/20 w-full transition-all cursor-text">
          <Search class="w-3.5 h-3.5 text-base-content/50 shrink-0 pointer-events-none" />
          <input
            ref="navbarSearchInputRef"
            v-model="servicesStore.searchKeyword"
            type="text"
            placeholder="搜索已纳管服务... (/ 快速聚焦)"
            class="grow text-xs bg-transparent border-none outline-none focus:outline-none p-0 min-w-0 placeholder:text-base-content/40"
            @focus="onSearchFocus"
            @keydown.esc="clearSearch"
          />
          <div class="flex items-center gap-1 shrink-0">
            <button
              v-if="servicesStore.searchKeyword"
              type="button"
              class="btn btn-ghost btn-xs btn-circle h-4 w-4 min-h-0 text-base-content/60 hover:text-base-content p-0"
              @click.stop="clearSearch"
              title="清空搜索"
            >
              ✕
            </button>
            <kbd v-else class="kbd kbd-xs bg-base-300/80 border-base-content/20 text-base-content/60 font-mono text-[10px] px-1.5 py-0.5 hidden sm:inline-flex">
              /
            </kbd>
          </div>
        </label>
      </div>

      <!-- Right: Hardware Monitor, Theme, Settings, Logout -->
      <div class="flex items-center gap-1.5 sm:gap-2 shrink-0">
        <!-- Hardware Monitor Popover Dropdown -->
        <div class="dropdown dropdown-end">
          <div tabindex="0" role="button" class="btn btn-ghost btn-xs sm:btn-sm gap-1.5 border border-base-content/10">
            <Activity class="w-4 h-4 text-primary animate-pulse" />
            <span class="hidden sm:inline font-medium">硬件监控</span>
            <span v-if="servicesStore.metrics" class="badge badge-xs badge-primary font-mono hidden md:inline">
              CPU {{ servicesStore.metrics.cpu.percent.toFixed(0) }}% · GPU {{ servicesStore.metrics.gpu.gpu_utilization_percent }}%
            </span>
          </div>
          <div 
            tabindex="0" 
            class="dropdown-content z-50 mt-2 p-3.5 shadow-2xl bg-base-100/95 backdrop-blur-md rounded-2xl w-80 sm:w-96 max-w-[95vw] border border-base-content/10 text-xs"
          >
            <HardwareMonitor :metrics="servicesStore.metrics" />
          </div>
        </div>

        <!-- Quick Theme Select -->
        <div class="dropdown dropdown-end">
          <div tabindex="0" role="button" class="btn btn-ghost btn-xs sm:btn-sm gap-1.5 border border-base-content/10">
            <Palette class="w-4 h-4 text-primary" />
            <span class="hidden md:inline font-medium">{{ currentThemeName }}</span>
          </div>
          <div 
            tabindex="0" 
            class="dropdown-content z-50 p-3 shadow-2xl bg-base-100/95 backdrop-blur-md rounded-2xl w-[320px] sm:w-[540px] max-w-[95vw] max-h-[75vh] overflow-y-auto border border-base-content/10 text-xs"
          >
            <div class="flex items-center justify-between pb-2 mb-2 border-b border-base-content/10">
              <span class="font-bold text-xs text-base-content/80 flex items-center gap-1.5">
                <Palette class="w-3.5 h-3.5 text-primary" />
                <span>DaisyUI 主题画廊 (全套 {{ themeStore.themes.length }} 款)</span>
              </span>
              <span class="badge badge-xs badge-primary font-mono">
                当前: {{ currentThemeName }}
              </span>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
              <button
                v-for="t in themeStore.themes"
                :key="t.id"
                type="button"
                :class="[
                  'flex items-center justify-between py-2 px-3 rounded-xl border text-left transition-all cursor-pointer',
                  themeStore.currentTheme === t.id
                    ? 'border-primary ring-2 ring-primary/40 bg-base-200 font-bold'
                    : 'border-base-content/5 hover:border-base-content/20 hover:bg-base-200/60 bg-base-200/20'
                ]"
                @click="themeStore.setTheme(t.id)"
              >
                <span class="truncate mr-2 text-xs">{{ t.name }}</span>
                <span class="flex items-center gap-1 shrink-0">
                  <span
                    v-for="(c, idx) in t.colors"
                    :key="idx"
                    class="w-2.5 h-2.5 rounded-full border border-black/20"
                    :style="{ backgroundColor: c }"
                  ></span>
                </span>
              </button>
            </div>
          </div>
        </div>

        <!-- Settings Link -->
        <router-link to="/settings" class="btn btn-ghost btn-sm btn-circle" title="系统设置与服务纳管">
          <Settings class="w-4 h-4" />
        </router-link>

        <!-- Logout -->
        <button class="btn btn-ghost btn-sm btn-circle text-error/80 hover:text-error" @click="logout" title="退出登录">
          <LogOut class="w-4 h-4" />
        </button>
      </div>
    </header>

    <!-- Global Toast Container -->
    <ToastContainer />

    <!-- Main Container -->
    <main class="flex-1 p-3 sm:p-6 md:p-8 max-w-7xl w-full mx-auto">
      <router-view />
    </main>

    <!-- Footer -->
    <footer class="text-center py-4 text-xs text-base-content/40 border-t border-base-content/5">
      UnitDeck &copy; 2026 - Headless AI & Systemd Control Hub
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { Cpu, Palette, Settings, LogOut, Activity, Search } from 'lucide-vue-next';
import { useAuthStore } from './stores/auth';
import { useThemeStore } from './stores/theme';
import { useServicesStore } from './stores/services';
import ToastContainer from './components/ToastContainer.vue';
import HardwareMonitor from './components/HardwareMonitor.vue';

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();
const themeStore = useThemeStore();
const servicesStore = useServicesStore();
const navbarSearchInputRef = ref<HTMLInputElement | null>(null);

function clearSearch() {
  servicesStore.searchKeyword = '';
  navbarSearchInputRef.value?.blur();
}

function onSearchFocus() {
  if (route.path !== '/') {
    router.push('/');
  }
}

function handleGlobalKeydown(e: KeyboardEvent) {
  const activeEl = document.activeElement;
  const isInput = activeEl?.tagName === 'INPUT' || activeEl?.tagName === 'TEXTAREA';
  
  if (e.key === '/' && !isInput) {
    e.preventDefault();
    if (route.path !== '/') {
      router.push('/').then(() => {
        navbarSearchInputRef.value?.focus();
        navbarSearchInputRef.value?.select();
      });
    } else {
      navbarSearchInputRef.value?.focus();
      navbarSearchInputRef.value?.select();
    }
  } else if (e.key === 'Escape') {
    if (servicesStore.searchKeyword) {
      servicesStore.searchKeyword = '';
    }
    navbarSearchInputRef.value?.blur();
  }
}

onMounted(() => {
  if (authStore.isAuthenticated) {
    servicesStore.startPolling(3000);
  }
  window.addEventListener('keydown', handleGlobalKeydown);
});

onUnmounted(() => {
  window.removeEventListener('keydown', handleGlobalKeydown);
});

const currentThemeName = computed(() => {
  const t = themeStore.themes.find((x) => x.id === themeStore.currentTheme);
  return t ? t.name : '主题';
});

function logout() {
  authStore.logout();
  router.push('/login');
}
</script>

