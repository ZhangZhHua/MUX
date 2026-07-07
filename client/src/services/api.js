import axios from 'axios';

const api = axios.create({
  baseURL: 'http://127.0.0.1:8000', // 后端 FastAPI 的本地地址
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

export default api;