export interface LogMessage {
  type?: 'log' | 'file-update' | 'run-complete';
  source: string;
  message: string;
  time_taken?: string;
}

export interface Phase {
  id: string;
  name: string;
  description: string;
  crews: string[];
  agents: string[];
  outputs: string[];
}

export interface RunRequest {
  base_url: string;
  instructions: string;
  force: boolean;
  headless: boolean;
  test_run_id?: string;
  phases: string[];
  target_pages: number;
  target_page_count: number;
}

export interface RunResponse {
  status: string;
  test_run_id: string;
  phases: string[];
  target_pages: number;
  phase_count: number;
  reason?: string;
  resume_from?: string;
  existing_pages?: number;
}

export interface PipelineStatus {
  test_run_id: string;
  overall_progress: string;
  phases: {
    [key: string]: {
      completed: boolean;
      outputs: string[];
      files_expected: string[];
    };
  };
  run_path: string;
  is_complete: boolean;
}
