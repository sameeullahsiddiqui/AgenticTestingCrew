import axios from 'axios';
import { RunRequest, RunResponse, Phase, PipelineStatus } from './types';

const BASE_URL = 'http://localhost:8000';

export const fetchPhases = async (): Promise<Phase[]> => {
  const res = await axios.get(`${BASE_URL}/phases`);
  return res.data.phases;
};

export const runPipeline = async (data: RunRequest): Promise<RunResponse> => {
  const res = await axios.post(`${BASE_URL}/run_pipeline`, data);
  return res.data;
};

export const resumePipeline = async (data: RunRequest): Promise<RunResponse> => {
  const res = await axios.post(`${BASE_URL}/resume_pipeline`, data);
  return res.data;
};

export const getPipelineStatus = async (testRunId: string): Promise<PipelineStatus> => {
  const res = await axios.get(`${BASE_URL}/pipeline-status/${testRunId}`);
  return res.data;
};

export const getRunIds = async (): Promise<string[]> => {
  const res = await axios.get(`${BASE_URL}/run-ids`);
  return res.data;
};

export const listFiles = async (runId: string) => {
  const res = await axios.get(`${BASE_URL}/list-files`, {
    params: { run_id: runId }
  });
  return res.data;
};

export const viewFile = (runId: string, filename: string) => {
  window.open(`${BASE_URL}/view?run_id=${runId}&filename=${filename}`, '_blank');
};

export const downloadFile = (runId: string, filename: string) => {
  window.open(`${BASE_URL}/download?run_id=${runId}&filename=${filename}`, '_blank');
};

export const llmCost = async () => {
  const res = await axios.get(`${BASE_URL}/usage`);
  return res.data;
};