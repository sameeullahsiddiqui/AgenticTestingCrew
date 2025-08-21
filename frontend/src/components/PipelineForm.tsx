// src/components/PipelineForm.tsx
import React, { useState, useEffect } from 'react';
import { runPipeline, resumePipeline, getRunIds } from '../api';
import { PlayCircle, RotateCcw } from 'lucide-react';
import { RunRequest } from '../types';
import PhaseSelector from './PhaseSelector';

const PipelineForm = () => {
  const [baseUrl, setBaseUrl] = useState('');
  const [testRunId, setTestRunId] = useState('');
  const [instructions, setInstructions] = useState('');
  const [forceRerun, setForceRerun] = useState(false);
  const [headless, setHeadless] = useState(true);
  const [targetPages, setTargetPages] = useState(100);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [selectedPhases, setSelectedPhases] = useState<string[]>(['exploration']);
  const [availableRunIds, setAvailableRunIds] = useState<string[]>([]);
  const [isResumeMode, setIsResumeMode] = useState(false);

  // Fetch available run IDs for resume functionality
  useEffect(() => {
    const fetchRunIds = async () => {
      try {
        const runIds = await getRunIds();
        setAvailableRunIds(runIds);
      } catch (error) {
        console.error('Failed to fetch run IDs:', error);
      }
    };
    fetchRunIds();
  }, []);

  const handleRun = async () => {
    if (!baseUrl.trim()) {
      setStatus('❌ Please enter a base URL');
      return;
    }
    
    if (selectedPhases.length === 0) {
      setStatus('❌ Please select at least one phase');
      return;
    }

    if (isResumeMode && !testRunId.trim()) {
      setStatus('❌ Please select a test run ID to resume');
      return;
    }

    setLoading(true);
    setStatus(null);

    try {
      const requestData: RunRequest = {
        base_url: baseUrl,
        instructions: instructions || 'Comprehensive testing of the application',
        force: forceRerun,
        headless: headless,
        test_run_id: testRunId,
        phases: selectedPhases,
        target_pages: targetPages,
        target_page_count: targetPages,
      };

      const result = isResumeMode 
        ? await resumePipeline(requestData)
        : await runPipeline(requestData);
      
      if (result.status === 'skipped') {
        setStatus(`⏭️ Pipeline skipped: ${result.test_run_id} (${result.reason})`);
      } else if (result.status === 'resumed') {
        setStatus(`🔄 Pipeline resumed: ${result.test_run_id} (from ${result.resume_from || 'beginning'})`);
      } else {
        setStatus(`✅ Pipeline started: ${result.test_run_id} (${result.phase_count} phases)`);
      }
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
        Test Configuration
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
                  placeholder="Tell me something about the application." />
      </div>

      <div className="mt-4">
        <label className="text-sm font-medium text-slate-300 block mb-1">Target Pages</label>
        <input className="form-input w-full placeholder-gray-400 text-white bg-black text-sm px-3 py-2 rounded border border-samee-yellow" 
               type="number"
               value={targetPages} 
               onChange={e => setTargetPages(parseInt(e.target.value) || 100)} 
               placeholder="100" 
               min="1" 
               max="1000" />
      </div>

      {/* Resume Mode Toggle */}
      <div className="mt-6">
        <label className="flex items-center gap-2 cursor-pointer">
          <div className={`toggle-switch ${isResumeMode ? 'active' : ''}`}>
            <div className="toggle-knob"></div>
          </div>
          <RotateCcw className="text-samee-yellow w-4 h-4" />
          <span className="text-sm">Resume existing run</span>
          <input 
            type="checkbox" 
            className="hidden" 
            checked={isResumeMode} 
            onChange={() => setIsResumeMode(!isResumeMode)} 
          />
        </label>
      </div>

      {/* Test Run ID Selector (only shown in resume mode) */}
      {isResumeMode && (
        <div className="mt-4">
          <label className="text-sm font-medium text-slate-300 block mb-1">Select Test Run to Resume</label>
          <select 
            className="form-select w-full placeholder-gray-400 text-white bg-black text-sm px-3 py-2 rounded border border-samee-yellow"
            value={testRunId} 
            onChange={e => setTestRunId(e.target.value)}
          >
            <option value="">Select a test run...</option>
            {availableRunIds.map(runId => (
              <option key={runId} value={runId}>
                {runId}
              </option>
            ))}
          </select>
          {availableRunIds.length === 0 && (
            <p className="text-xs text-slate-400 mt-1">No previous runs found</p>
          )}
        </div>
      )}

      <div className="mt-6">
        <PhaseSelector 
          selectedPhases={selectedPhases} 
          onPhasesChange={setSelectedPhases} 
        />
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
        {loading 
          ? '⏳ Running...' 
          : isResumeMode 
            ? '🔄 Resume Pipeline' 
            : '🚀 Run Pipeline'
        }
      </button>

      {status && <div className="mt-4 text-sm text-gray-300">{status}</div>}
    </div>
  );
};

export default PipelineForm;
