import axios from 'axios';

const API_BASE_URL = '/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Cluster API
export const clusterApi = {
  getStatus: () => api.get('/cluster/status'),
  getMetrics: () => api.get('/cluster/metrics'),
  getTopology: () => api.get('/cluster/topology'),
};

// Hosts API
export const hostsApi = {
  listHosts: () => api.get('/hosts'),
  getHost: (hostName: string) => api.get(`/hosts/${hostName}`),
  getHostVMs: (hostName: string) => api.get(`/hosts/${hostName}/vms`),
};

// VMs API
export const vmsApi = {
  listVMs: () => api.get('/vms'),
  getVM: (uuid: string) => api.get(`/vms/${uuid}`),
  createVM: (data: any) => api.post('/vms', data),
  startVM: (uuid: string) => api.post(`/vms/${uuid}/start`),
  stopVM: (uuid: string, force: boolean = false) => api.post(`/vms/${uuid}/stop`, { force }),
  pauseVM: (uuid: string) => api.post(`/vms/${uuid}/pause`),
  resumeVM: (uuid: string) => api.post(`/vms/${uuid}/resume`),
  deleteVM: (uuid: string) => api.delete(`/vms/${uuid}`),
  getVMStats: (uuid: string) => api.get(`/vms/${uuid}/stats`),
};

// Networks API
export const networksApi = {
  listSwitches: () => api.get('/networks/switches'),
  createSwitch: (data: any) => api.post('/networks/switches', data),
  deleteSwitch: (name: string) => api.delete(`/networks/switches/${name}`),

  listRouters: () => api.get('/networks/routers'),
  createRouter: (data: any) => api.post('/networks/routers', data),
  deleteRouter: (name: string) => api.delete(`/networks/routers/${name}`),

  connectRouterSwitch: (data: any) => api.post('/networks/connect', data),

  createACL: (data: any) => api.post('/networks/acls', data),

  listLoadBalancers: () => api.get('/networks/load-balancers'),
  createLoadBalancer: (data: any) => api.post('/networks/load-balancers', data),
  deleteLoadBalancer: (name: string) => api.delete(`/networks/load-balancers/${name}`),

  listBridges: () => api.get('/networks/bridges'),
  getBridgeInfo: (name: string) => api.get(`/networks/bridges/${name}`),

  getTopology: () => api.get('/networks/topology'),
};

export default api;
