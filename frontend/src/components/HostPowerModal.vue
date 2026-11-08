<template>
  <div>
    <!-- DaisyUI Modal Dialog -->
    <dialog class="modal modal-bottom sm:modal-middle" :class="{ 'modal-open': modelValue && !isProcessing }">
      <div class="modal-box border border-base-content/10 shadow-2xl bg-base-100 max-w-md p-6 space-y-4">
        <!-- Header Icon & Title -->
        <div class="flex items-center gap-3">
          <div 
            class="p-3 rounded-2xl flex items-center justify-center"
            :class="action === 'poweroff' ? 'bg-error/15 text-error ring-4 ring-error/10' : 'bg-warning/15 text-warning ring-4 ring-warning/10'"
          >
            <PowerOff v-if="action === 'poweroff'" class="w-6 h-6 animate-pulse" />
            <RotateCw v-else class="w-6 h-6 animate-spin-slow" />
          </div>
          <div>
            <h3 class="font-bold text-lg">
              {{ action === 'poweroff' ? '确认关闭宿主机？' : '确认重启宿主机？' }}
            </h3>
            <p class="text-xs text-base-content/60">
              {{ action === 'poweroff' ? '硬件级系统关闭 (Poweroff)' : '系统重新引导 (System Reboot)' }}
            </p>
          </div>
        </div>

        <!-- Warning Callout Box -->
        <div 
          class="p-3.5 rounded-xl text-xs space-y-1.5 border"
          :class="action === 'poweroff' ? 'bg-error/10 border-error/20 text-error' : 'bg-warning/10 border-warning/20 text-warning'"
        >
          <div class="font-bold flex items-center gap-1.5">
            <AlertTriangle class="w-4 h-4 shrink-0" />
            <span>重要影响与安全警示</span>
          </div>
          <ul class="list-disc list-inside space-y-1 opacity-90 text-[11px] leading-relaxed">
            <li v-if="action === 'poweroff'">
              关机后 UnitDeck 控制台将<strong>立即完全离线</strong>。
            </li>
            <li v-if="action === 'poweroff'">
              <strong>Web 界面无法远程开机</strong>，必须亲自到物理机前按下机箱电源按键！
            </li>
            <li v-if="action === 'reboot'">
              正在执行的 AI 推理、训练及后台任务将<strong>强制中断</strong>。
            </li>
            <li>系统所有受管的后台 systemd 服务将统一收到停止信号。</li>
          </ul>
        </div>

        <!-- Lock Control for Poweroff: Keyword Input -->
        <div v-if="action === 'poweroff'" class="space-y-1.5 pt-1">
          <label class="text-xs font-semibold text-base-content/80 flex items-center justify-between">
            <span>请输入 <code class="badge badge-sm badge-error font-mono font-bold">SHUTDOWN</code> 以解锁关机：</span>
          </label>
          <input 
            v-model="confirmKeyword"
            type="text"
            placeholder="输入 SHUTDOWN"
            class="input input-bordered input-sm w-full font-mono text-center tracking-widest uppercase focus:border-error focus:ring-1 focus:ring-error"
            @keyup.enter="canSubmit && handleConfirm()"
          />
        </div>

        <!-- Lock Control for Reboot: Countdown Note -->
        <div v-if="action === 'reboot' && countdown > 0" class="text-center py-1">
          <span class="text-xs text-base-content/50 font-medium">
            防手抖保护锁定中，请稍候 <span class="font-bold text-warning font-mono">{{ countdown }}</span> 秒...
          </span>
        </div>

        <!-- Actions -->
        <div class="modal-action flex items-center justify-end gap-2 pt-2 border-t border-base-content/10">
          <button 
            type="button" 
            class="btn btn-ghost btn-sm"
            @click="handleCancel"
          >
            取消返回
          </button>

          <button 
            v-if="action === 'poweroff'"
            type="button"
            class="btn btn-error btn-sm gap-1.5 shadow-sm"
            :disabled="!canSubmit"
            @click="handleConfirm"
          >
            <PowerOff class="w-4 h-4" />
            <span>执行关闭宿主机</span>
          </button>

          <button 
            v-else
            type="button"
            class="btn btn-warning btn-sm gap-1.5 shadow-sm"
            :disabled="!canSubmit"
            @click="handleConfirm"
          >
            <RotateCw class="w-4 h-4" />
            <span>{{ countdown > 0 ? `确认重启 (${countdown}s)` : '确认重启宿主机' }}</span>
          </button>
        </div>
      </div>
      <form method="dialog" class="modal-backdrop" @click="handleCancel">
        <button>close</button>
      </form>
    </dialog>

    <!-- Full-screen Processing Overlay during Reboot/Poweroff -->
    <div 
      v-if="isProcessing" 
      class="fixed inset-0 z-[9999] bg-base-300/90 backdrop-blur-md flex flex-col items-center justify-center p-6 text-center select-none"
    >
      <div class="card bg-base-100 shadow-2xl border border-base-content/10 max-w-md w-full p-8 space-y-6">
        <div class="flex justify-center">
          <div 
            class="p-5 rounded-full"
            :class="action === 'poweroff' ? 'bg-error/20 text-error' : 'bg-warning/20 text-warning'"
          >
            <PowerOff v-if="action === 'poweroff'" class="w-12 h-12" />
            <RotateCw v-else class="w-12 h-12 animate-spin" />
          </div>
        </div>

        <div class="space-y-2">
          <h2 class="text-xl font-bold">
            {{ action === 'poweroff' ? '宿主机已下达关机指令' : '宿主机正在重启中...' }}
          </h2>
          <p class="text-xs text-base-content/60 leading-relaxed">
            <template v-if="action === 'poweroff'">
              关机信号已成功送达系统。宿主机将立即切断电源并离线，您可以安全关闭当前浏览器窗口。
            </template>
            <template v-else>
              正在等待系统引导并恢复后台守护进程，UnitDeck 正在自动尝试重新建立连接 (尝试次数: {{ retryCount }})
            </template>
          </p>
        </div>

        <div v-if="action === 'reboot'" class="flex items-center justify-center gap-2 text-xs font-mono text-primary font-semibold">
          <span class="loading loading-spinner loading-sm"></span>
          <span>心跳重连探测中...</span>
        </div>

        <div v-if="action === 'poweroff'" class="pt-2">
          <div class="badge badge-neutral text-xs py-3 px-4">
            主机已断电 · 请于物理机前重新按键开机
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from 'vue';
import { PowerOff, RotateCw, AlertTriangle } from 'lucide-vue-next';
import api from '../api/client';
import { useToastStore } from '../stores/toast';

const props = defineProps<{
  modelValue: boolean;
  action: 'reboot' | 'poweroff' | null;
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void;
  (e: 'confirmed', action: 'reboot' | 'poweroff'): void;
}>();

const toastStore = useToastStore();

const confirmKeyword = ref('');
const countdown = ref(0);
let countdownTimer: any = null;

const isProcessing = ref(false);
const retryCount = ref(0);
let pollTimer: any = null;

const canSubmit = computed(() => {
  if (props.action === 'poweroff') {
    return confirmKeyword.value.trim().toUpperCase() === 'SHUTDOWN';
  }
  if (props.action === 'reboot') {
    return countdown.value <= 0;
  }
  return false;
});

watch(() => props.modelValue, (isOpen) => {
  if (isOpen) {
    confirmKeyword.value = '';
    if (props.action === 'reboot') {
      countdown.value = 3;
      clearInterval(countdownTimer);
      countdownTimer = setInterval(() => {
        if (countdown.value > 0) {
          countdown.value--;
        } else {
          clearInterval(countdownTimer);
        }
      }, 1000);
    }
  } else {
    clearInterval(countdownTimer);
  }
});

function handleCancel() {
  if (isProcessing.value) return;
  emit('update:modelValue', false);
}

async function handleConfirm() {
  if (!props.action || !canSubmit.value) return;

  const targetAction = props.action;
  isProcessing.value = true;

  try {
    const endpoint = targetAction === 'poweroff' ? '/system/host/poweroff' : '/system/host/reboot';
    await api.post(endpoint);
    emit('confirmed', targetAction);

    if (targetAction === 'reboot') {
      startRebootPolling();
    }
  } catch (err: any) {
    isProcessing.value = false;
    emit('update:modelValue', false);
    toastStore.error(err.response?.data?.detail || '执行宿主机电源控制失败');
  }
}

function startRebootPolling() {
  retryCount.value = 0;
  clearInterval(pollTimer);
  
  // Wait 10 seconds before starting to poll (giving machine time to go down and start up)
  setTimeout(() => {
    pollTimer = setInterval(async () => {
      retryCount.value++;
      try {
        const res = await api.get('/system/metrics', { timeout: 2000 });
        if (res.status === 200) {
          clearInterval(pollTimer);
          isProcessing.value = false;
          emit('update:modelValue', false);
          toastStore.success('宿主机已成功重启并恢复在线！');
          window.location.reload();
        }
      } catch (e) {
        // Continue polling until host is back
      }
    }, 3000);
  }, 10000);
}

onUnmounted(() => {
  clearInterval(countdownTimer);
  clearInterval(pollTimer);
});
</script>

<style scoped>
@keyframes spin-slow {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
.animate-spin-slow {
  animation: spin-slow 8s linear infinite;
}
</style>

