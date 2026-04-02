const { contextBridge } = require('electron');

contextBridge.exposeInMainWorld('navagatorDesktop', {
  platform: 'electron',
  apiBase: process.env.NAVAGATOR_API_BASE || 'http://127.0.0.1:8000'
});
