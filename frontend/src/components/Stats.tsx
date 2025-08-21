import React from 'react';
import { Activity } from 'lucide-react';

const Stats = () => (
  <div className="card bg-slate-800 bg-opacity-50 rounded-xl p-6 border border-slate-700">
    <h3 className="text-xl font-semibold flex items-center gap-3 mb-4">
      <Activity className="text-samee-yellow w-5 h-5" />
      Statistics
    </h3>
    <div className="space-y-2">
      <div className="flex justify-between">
        <span>Total Runs</span>
        <span className="font-bold">127</span>
      </div>
      {/* <div className="flex justify-between">
        <span>Success Rate</span>
        <span className="text-emerald-400 font-bold">94.2%</span>
      </div> */}
      <div className="flex justify-between">
        <span>Avg Duration</span>
        <span className="font-bold">2m 34s</span>
      </div>
      <div className="flex justify-between">
        <span>Active Agents</span>
        <span className="text-indigo-400 font-bold">1</span>
      </div>
    </div>
  </div>
);

export default Stats;