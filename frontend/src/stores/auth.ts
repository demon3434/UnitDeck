import { defineStore } from 'pinia';
import { ref } from 'vue';
import api from '../api/client';

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string>(localStorage.getItem('unitdeck_token') || '');
  const username = ref<string>(localStorage.getItem('unitdeck_username') || '');
  const isAuthenticated = ref<boolean>(!!token.value);

  async function login(user: string, pass: string): Promise<{ success: boolean; error?: string }> {
    try {
      const res = await api.post('/auth/login', { username: user, password: pass });
      token.value = res.data.token;
      username.value = res.data.username;
      isAuthenticated.value = true;
      localStorage.setItem('unitdeck_token', token.value);
      localStorage.setItem('unitdeck_username', username.value);
      return { success: true };
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      if (err.response?.status === 429) {
        return { success: false, error: detail || '登录失败次数过多，已被暂时锁定，请稍后再试' };
      }
      return { success: false, error: detail || '用户名或密码错误，请重试' };
    }
  }

  async function logout() {
    try {
      await api.post('/auth/logout');
    } catch {
      // Ignore network errors on logout
    } finally {
      token.value = '';
      username.value = '';
      isAuthenticated.value = false;
      localStorage.removeItem('unitdeck_token');
      localStorage.removeItem('unitdeck_username');
    }
  }

  async function checkAuth(): Promise<boolean> {
    if (!token.value) {
      await logout();
      return false;
    }
    try {
      const res = await api.get('/auth/me');
      username.value = res.data.username;
      isAuthenticated.value = true;
      return true;
    } catch {
      await logout();
      return false;
    }
  }

  return { token, username, isAuthenticated, login, logout, checkAuth };
});
