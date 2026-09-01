import axios from 'axios';
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
const api = axios.create({ baseURL: API_BASE, headers: { 'Content-Type': 'application/json' } });
api.interceptors.request.use(config => {
  const token = localStorage.getItem('mmx_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});
api.interceptors.response.use((res) => res, async (err) => {
  if (err.response?.status === 401 && !err.config._retry) {
    err.config._retry = true;
    const refreshToken = localStorage.getItem('mmx_refresh');
    if (refreshToken) {
      try {
        const { data } = await axios.post(`${API_BASE}/auth/refresh`, { token: refreshToken });
        localStorage.setItem('mmx_token', data.access_token);
        err.config.headers.Authorization = `Bearer ${data.access_token}`;
        return api(err.config);
      } catch { window.location.href = '/login'; }
    }
  }
  return Promise.reject(err);
});
export default api;
export const AuthAPI = {
  register: (email, password, fullName, company) => api.post('/auth/register', { email, password, full_name: fullName, company }),
  login: (email, password) => api.post('/auth/login', { email, password }),
  me: () => api.get('/auth/me'),
};
export const FileAPI = {
  upload: (file) => { const fd = new FormData(); fd.append('file', file); return api.post('/files/upload', fd, { headers: { 'Content-Type': 'multipart/form-data' } }); },
  voxelize: (fp, gx, gy, gz, dim) => api.post('/files/voxelize', { filepath: fp, grid_x: gx, grid_y: gy, grid_z: gz, dimension: dim }),
};
export const SimulationAPI = {
  create: (cfg) => api.post('/simulations/', cfg),
  get: (id) => api.get(`/simulations/${id}`),
  getResults: (id) => api.get(`/simulations/${id}/results`),
  list: () => api.get('/simulations/'),
};
export const GeometryAPI = {
  list: () => api.get('/geometries/'),
  generate: (id, gridSize) => api.post(`/geometries/${id}/generate`, { grid_size: gridSize }),
};