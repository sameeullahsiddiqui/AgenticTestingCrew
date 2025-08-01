import axios from 'axios';

const BASE_URL = 'http://localhost:8000';

export const fetchAgents = async () => {
  const res = await axios.get(`${BASE_URL}/agents`);
  return res.data.agents;
};

export const runPipeline = async (data: any) => {
  const res = await axios.post(`${BASE_URL}/run_pipeline`, data);
  return res.data;
};

export const listFiles = async (runId: string) => {
  const res = await axios.get(`${BASE_URL}/list-files`, {
    params: { run_id: runId }
  });
  return res.data;
};

export const downloadFile = (filename: string) => {
  window.open(`${BASE_URL}/download/${filename}`, '_blank');
};

export const llmCost = async () => {
  const res = await axios.get(`${BASE_URL}/usage`);
  return res.data;
};