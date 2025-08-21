import React, { useEffect, useState } from "react";
import { Activity } from "lucide-react";
import axios from "axios";
import { llmCost } from "../api";

interface UsageData {
  model: string;
  tokensUsed: number;
  costUSD: number;
  date: string;
}

const Dashboard = () => {
  const [usage, setUsage] = useState<UsageData[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedModel, setSelectedModel] = useState<string>("all");

  useEffect(() => {
    const fetchUsage = async () => {
      setLoading(true);
      try {
        const response = await llmCost();
        setUsage(Array.isArray(response.data) ? response.data : []);
      } catch (error) {
        console.error("Failed to fetch usage data:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchUsage();
  }, []);

  const filteredUsage = selectedModel === "all"
    ? usage
    : usage.filter(u => u.model === selectedModel);

  const totalTokens = Array.isArray(filteredUsage)
    ? filteredUsage.reduce((acc, u) => acc + u.tokensUsed, 0)
    : 0;

  const totalCost = Array.isArray(filteredUsage)
    ? filteredUsage.reduce((acc, u) => acc + u.costUSD, 0)
    : 0;

  const models = Array.from(new Set(usage.map(u => u.model)));

  return (
    <div>      
      {loading ? (
        <div style={{ textAlign: 'center', color: 'gray', marginTop: '1rem' }}>Loading usage data, please wait...</div>
      ) : (
        <div>
          {/* <div style={{ marginBottom: '1rem' }}>
            <button onClick={() => setSelectedModel('all')} style={{ marginRight: '0.5rem' }}>All Models</button>
            {models.map(model => (
              <button key={model} onClick={() => setSelectedModel(model)} style={{ marginRight: '0.5rem' }}>{model}</button>
            ))}
          </div> */}

          {/* Stats Card Replacement for Cost */}
          <div className="card bg-slate-800 bg-opacity-50 rounded-xl p-6 border border-slate-700 mb-6" style={{ color: '#fff' }}>
            <h3 className="text-xl font-semibold flex items-center gap-3 mb-4">
              <Activity className="text-yellow-400 w-5 h-5" />
              Cost
            </h3>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span>Total Cost</span>
                <span className="font-bold">${totalCost.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span>Total Tokens</span>
                <span className="font-bold">{totalTokens.toLocaleString()}</span>
              </div>
            </div>
          </div>

          <div style={{ marginTop: '1.5rem' }}>
            {filteredUsage.map((u, i) => (
              <div key={i} style={{ border: '1px solid #ccc', borderRadius: '8px', padding: '1rem', marginBottom: '1rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <div>
                    <p style={{ fontWeight: '600' }}>{u.date}</p>
                    <p style={{ fontSize: '0.875rem', color: '#6b7280' }}>Model: {u.model}</p>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <p style={{ fontWeight: 'bold' }}>{u.tokensUsed.toLocaleString()} tokens</p>
                    <p style={{ color: '#16a34a' }}>${u.costUSD.toFixed(4)}</p>
                  </div>
                </div>
                <div style={{ backgroundColor: '#e5e7eb', borderRadius: '4px', overflow: 'hidden', marginTop: '0.5rem' }}>
                  <div style={{ width: `${(u.tokensUsed / totalTokens) * 100}%`, backgroundColor: '#2563eb', height: '8px' }}></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;