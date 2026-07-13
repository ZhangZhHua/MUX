import axios from 'axios';

const AUTH_STORAGE_KEYS = ['token', 'role', 'userName', 'userId'];
let redirectingToLogin = false;

const clearStoredAuthentication = () => {
  AUTH_STORAGE_KEYS.forEach((key) => localStorage.removeItem(key));
};

const redirectToLogin = () => {
  if (redirectingToLogin || window.location.pathname === '/login') return;

  redirectingToLogin = true;
  const currentPath = `${window.location.pathname}${window.location.search}${window.location.hash}`;
  const loginUrl = new URL('/login', window.location.origin);
  loginUrl.searchParams.set('redirect', currentPath);
  window.location.replace(loginUrl.toString());
};

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
});

// 请求拦截器：自动为每个请求附加 JWT Token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Expired or invalid JWTs should end the stale client session immediately.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && localStorage.getItem('token')) {
      clearStoredAuthentication();
      redirectToLogin();
    }
    return Promise.reject(error);
  }
);

export default api;
