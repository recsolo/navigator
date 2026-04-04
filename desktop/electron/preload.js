const { contextBridge } = require('electron');

const desktopBridge = {
  platform: 'electron',
  apiBase:
    process.env.NAVIGATOR_API_BASE ||
    process.env.NAVAGATOR_API_BASE ||
    'http://127.0.0.1:8000'
};

contextBridge.exposeInMainWorld('navigatorDesktop', desktopBridge);
contextBridge.exposeInMainWorld('navagatorDesktop', desktopBridge);
