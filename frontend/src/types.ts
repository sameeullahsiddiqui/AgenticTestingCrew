export interface LogMessage {
  type?: 'log' | 'file-update' | 'run-complete';
  source: string;
  message: string;
  time_taken?: string;
}
