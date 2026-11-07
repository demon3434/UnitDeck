import { defineStore } from 'pinia';
import { ref } from 'vue';
import api from '../api/client';

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string>(localStorage.getItem('unitdeck_token') || '');
  const username = ref<string>(localStorage.getItem('unitdeck_username') || '');
  const isAuthenticated = ref<boolean>(!!token.value);

  async function login(user: string, pass: string): Promise<boolean> {
    try {
      const res = await api.post('/auth/login', { username: user, password: pass });
      token.value = res.data.token;
      username.value = res.data.username;
      isAuthenticated.value = true;
      localStorage.setItem('unitdeck_token', token.value);
      localStorage.setItem('unitdeck_username', username.value);
      return true;
    } catch {
      return false;
    }
  }

  function logout() {
    token.value = '';
    username.value = '';
    isAuthenticated.value = false;
    localStorage.removeItem('unitdeck_token');
    localStorage.removeItem('unitdeck_username');
  }

  async function checkAuth(): Promise<boolean> {
    if (!token.value) {
      logout();
      return false;
    }
    try {
      const res = await api.get('/auth/me');
      username.value = res.data.username;
      isAuthenticated.value = true;
      return true;
    } catch {
      logout();
      return false;
    }
  }

  return { token, username, isAuthenticated, login, logout, checkAuth };
});

