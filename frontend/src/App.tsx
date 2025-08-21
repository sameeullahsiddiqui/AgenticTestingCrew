import React, { useEffect, useRef, useState } from 'react';
import Header from './components/Header';
import PipelineForm from './components/PipelineForm';
// import AgentSelector from './components/AgentSelector';
import LiveLogs from './components/LiveLogs';
import OutputFiles from './components/OutputFiles';
import Stats from './components/Stats';
import { connectWebSocket } from './websocket';
import { LogMessage } from './types';
import axios from 'axios';
import Dashboard from './components/UsageDashboard';

const config = {
  apiBase: import.meta.env.VITE_API_BASE || 'http://localhost:8000',
  wsUrl: import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/logs',
};


function App() {
  const [logs, setLogs] = useState<LogMessage[]>([]);
  const [refreshCounter, setRefreshCounter] = useState(0);
  const [filter, setFilter] = useState('');
  const [isSystemOnline, setIsSystemOnline] = useState<boolean>(false);
  const [runIds, setRunIds] = useState<string[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<string>('');
  const wsRef = useRef<WebSocket | null>(null);

  const fetchRunIds = async () => {
    try {
      const res = await axios.get(`${config.apiBase}/run-ids`);
      setRunIds(res.data);
    } catch {
      setRunIds([]);
    }
  };

  useEffect(() => {
    fetchRunIds();
    const interval = setInterval(() => {
      fetchRunIds();
    }, 100000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const ws = new WebSocket(config.wsUrl);
    wsRef.current = ws;

    let alive = true;

    ws.onopen = () => {
      console.log('✅ WebSocket connected');
      if (alive) setIsSystemOnline(true);
    };

    ws.onclose = () => {
      console.warn('🔌 WebSocket disconnected');
      if (alive) setIsSystemOnline(false);
    };

    ws.onerror = (err) => {
      console.error('❌ WebSocket error:', err);
      if (alive) setIsSystemOnline(false);
    };

    ws.onmessage = (event) => {
      try {
        const data: LogMessage = JSON.parse(event.data);
        if (data.type === 'log' || !data.type) {
          setLogs((prev) => [...prev, data]);
        } else if (data.type === 'file-update') {
          setRefreshCounter((prev) => prev + 1);
        }
      } catch (error) {
        console.error('⚠ WebSocket message error:', error);
      }
    };

    return () => {
      alive = false;
      ws.close();
    };
}, []);


const filteredLogs = logs.filter((log) => {
  if (!filter) return true;

  const lowerFilter = filter.toLowerCase();

  if (typeof log === 'string') {
    return log.toLowerCase().includes(lowerFilter);
  }

  const message = typeof log.message === 'string' ? log.message.toLowerCase() : '';
  const source = typeof log.source === 'string' ? log.source.toLowerCase() : '';

  return message.includes(lowerFilter) || source.includes(lowerFilter);
});


{/* <LiveLogs logs={logs} /> */}

  return (
    <div className="min-h-screen bg-samee-black text-samee-yellow">
      <Header status={isSystemOnline ? 'Online' : 'Offline'} />
      <main className="p-6 max-w-7xl mx-auto grid grid-cols-3 gap-4">
        <div className="col-span-2 space-y-4">
          <PipelineForm />
          {/* <AgentSelector /> */}
          <div className="card">
            <input
              type="text"
              placeholder="Filter logs by agent or keyword..."
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="w-full mb-4 placeholder-gray-400 text-white bg-black text-sm px-3 py-2 rounded border border-samee-yellow"
            />
            <LiveLogs logs={filteredLogs} />
          </div>
        </div>
        <div className="col-span-1 space-y-4">
          <div className="card">
            <label className="block mb-2">Select Run ID</label>
            <select
              value={selectedRunId}
              onChange={(e) => setSelectedRunId(e.target.value)}
              className="w-full mb-4"
            >
              <option value="">-- Select a Run ID --</option>
              {runIds.map((id) => (
                <option key={id} value={id}>{id}</option>
              ))}
            </select>
            {selectedRunId && <OutputFiles refreshSignal={refreshCounter} runId={selectedRunId} />}
          </div>
          <Stats />
          <Dashboard />
        </div>
      </main>
    </div>
  );
}

export default App;
