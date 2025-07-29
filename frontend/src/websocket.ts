import { LogMessage } from './types';

export const connectWebSocket = (
  url: string,
  onMessage: (data: LogMessage) => void,
  onClose?: () => void
) => {
  const ws = new WebSocket(url);

  ws.onopen = () => console.log('✅ WebSocket connected');

  ws.onmessage = (event: MessageEvent) => {
    try {
      const data: LogMessage = JSON.parse(event.data);
      onMessage(data);
    } catch (e) {
      console.error('Error parsing WebSocket message:', e);
    }
  };

  ws.onclose = () => {
    console.warn('🔌 WebSocket disconnected');
    onClose?.();
    setTimeout(() => connectWebSocket(url, onMessage, onClose), 3000);
  };

  return ws;
};