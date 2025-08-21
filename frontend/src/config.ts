// src/config.ts

export const config = {
  apiBase: import.meta.env.VITE_API_BASE || 'http://localhost:8000',
  wsUrl: import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/logs',
};
