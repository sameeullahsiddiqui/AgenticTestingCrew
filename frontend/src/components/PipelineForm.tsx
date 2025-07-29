// src/components/PipelineForm.tsx
import React, { useEffect, useState } from 'react';
import { runPipeline, fetchAgents } from '../api';
import { PlayCircle } from 'lucide-react';
import { Users } from 'lucide-react';

const PipelineForm = () => {
  const [baseUrl, setBaseUrl] = useState('');
  const [testRunId, setTestRunId] = useState('');
  const [instructions, setInstructions] = useState('');
  const [forceRerun, setForceRerun] = useState(false);
  const [headless, setHeadless] = useState(true);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [agents, setAgents] = useState<{ id: string }[]>([]);
  const [selectedAgents, setSelectedAgents] = useState<string[]>(() => {
    const stored = localStorage.getItem('selectedAgents');
    return stored ? JSON.parse(stored) : [];
  });

  useEffect(() => {
    fetchAgents().then(setAgents);
  }, []);

  useEffect(() => {
    localStorage.setItem('selectedAgents', JSON.stringify(selectedAgents));
  }, [selectedAgents]);

  const toggleAgent = (agentId: string) => {
    setSelectedAgents((prev) =>
      prev.includes(agentId) ? prev.filter(id => id !== agentId) : [...prev, agentId]
    );
  };

  const handleRun = async () => {
    setLoading(true);
    setStatus(null);

    try {
      const result = await runPipeline({
        base_url: baseUrl,
        instructions,
        force: forceRerun,
        headless: headless,
        agents_to_run: selectedAgents,
        test_run_id: testRunId,
      });
      setStatus(`✅ Pipeline started: ${result.test_run_id}`);
    } catch (error) {
      console.error(error);
      setStatus('❌ Error triggering pipeline');
    }

    setLoading(false);
  };

  return (
    <div className="card bg-slate-800 bg-opacity-50 rounded-xl p-6 border border-slate-700">
      <h2 className="text-xl font-semibold flex items-center gap-3 mb-4">
         <PlayCircle className="text-samee-yellow w-5 h-5" />
        Pipeline Configuration
      </h2>

      {/* <div className="grid grid-cols-2 gap-4"> */}
      <div className="mt-4">
        <div>
          <label className="text-sm font-medium text-slate-300 block mb-1">Application URL</label>
          <input className="form-input w-full placeholder-gray-400 text-white bg-black text-sm px-3 py-2 rounded border border-samee-yellow" 
                 value={baseUrl} onChange={e => setBaseUrl(e.target.value)} 
                 placeholder="https://www.saucedemo.com/" />
        </div>
        {/* <div>
          <label className="text-sm font-medium text-slate-300 block mb-1">Test Run ID</label>
          <input className="form-input w-full placeholder-gray-400 text-white bg-black text-sm px-3 py-2 rounded border border-samee-yellow"  
                 value={testRunId} onChange={e => setTestRunId(e.target.value)} 
                 placeholder="run_001" />
        </div> */}
      </div>

      <div className="mt-4">
        <label className="text-sm font-medium text-slate-300 block mb-1">Instructions</label>
        <textarea className="form-textarea w-full min-h-[100px] placeholder-gray-400 text-white bg-black text-sm px-3 py-2 rounded border border-samee-yellow" 
                  value={instructions} onChange={e => setInstructions(e.target.value)} 
                  placeholder="tell me something about application." />
      </div>

      <div className="mt-6">
         <h3 className="text-xl font-semibold flex items-center gap-3 mb-4">
            <Users className="text-samee-yellow w-5 h-5" />
            Select Agents
        </h3>

        <div className="flex flex-wrap gap-2">
          {agents.map(agent => (
            <button
              key={agent.id}
              onClick={() => toggleAgent(agent.id)}
              className={`px-3 py-1 rounded-full border text-sm ${selectedAgents.includes(agent.id) ? 'bg-indigo-600 border-indigo-400 text-white' : 'bg-slate-700 border-slate-600 text-slate-300'}`}
            >
              {agent.id}
            </button>
          ))}
        </div>
      </div>

      <div className="flex gap-6 mt-6">
        <label className="flex items-center gap-2 cursor-pointer">
          <div className={`toggle-switch ${forceRerun ? 'active' : ''}`}>
            <div className="toggle-knob"></div>
          </div>
          <span className="text-sm">Force Rerun</span>
          <input type="checkbox" className="hidden" checked={forceRerun} onChange={() => setForceRerun(!forceRerun)} />
        </label>

        <label className="flex items-center gap-2 cursor-pointer">
          <div className={`toggle-switch ${headless ? 'active' : ''}`}>
            <div className="toggle-knob"></div>
          </div>
          <span className="text-sm">Hide browser</span>
          <input type="checkbox" className="hidden" checked={headless} onChange={() => setHeadless(!headless)} />
        </label>
      </div>

      <button
        className="run-button mt-6 disabled:bg-slate-600 disabled:cursor-not-allowed"
        onClick={handleRun}
        disabled={loading}
      >
        {loading ? '⏳ Running...' : '🚀 Run Pipeline'}
      </button>

      {status && <div className="mt-4 text-sm text-gray-300">{status}</div>}
    </div>
  );
};

export default PipelineForm;
