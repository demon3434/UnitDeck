<template>
  <div class="min-h-screen flex items-center justify-center p-4 bg-base-300">
    <div class="card w-full max-w-sm bg-base-100 shadow-xl border border-base-content/10">
      <div class="card-body p-6 sm:p-8">
        <div class="text-center space-y-2 mb-4">
          <div class="inline-flex p-3 rounded-2xl bg-primary/10 text-primary">
            <Cpu class="w-8 h-8" />
          </div>
          <h1 class="text-2xl font-black tracking-tight">UnitDeck</h1>
          <p class="text-xs text-base-content/60">AI 服务与显存管理控制台</p>
        </div>

        <form @submit.prevent="handleLogin" class="space-y-4">
          <div class="form-control">
            <label class="label">
              <span class="label-text text-xs font-medium">管理员用户名</span>
            </label>
            <input 
              v-model="username" 
              type="text" 
              placeholder="默认 admin" 
              class="input input-bordered w-full input-sm sm:input-md" 
              required 
            />
          </div>

          <div class="form-control">
            <label class="label">
              <span class="label-text text-xs font-medium">登录密码</span>
            </label>
            <input 
              v-model="password" 
              type="password" 
              placeholder="默认 admin123" 
              class="input input-bordered w-full input-sm sm:input-md" 
              required 
            />
          </div>

          <div v-if="errorMsg" class="alert alert-error text-xs p-2.5 rounded-lg">
            <span>{{ errorMsg }}</span>
          </div>

          <button 
            type="submit" 
            class="btn btn-primary w-full mt-2" 
            :disabled="loading"
          >
            <span v-if="loading" class="loading loading-spinner loading-sm"></span>
            <span v-else>进入控制台</span>
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { Cpu } from 'lucide-vue-next';
import { useAuthStore } from '../stores/auth';

const router = useRouter();
const authStore = useAuthStore();

const username = ref('admin');
const password = ref('');
const loading = ref(false);
const errorMsg = ref('');

async function handleLogin() {
  loading.value = true;
  errorMsg.value = '';
  const success = await authStore.login(username.value, password.value);
  loading.value = false;
  if (success) {
    router.push('/');
  } else {
    errorMsg.value = '用户名或密码错误，请重试';
  }
}
</script>

