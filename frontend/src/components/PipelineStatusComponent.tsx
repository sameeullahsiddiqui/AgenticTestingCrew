import React, { useState, useEffect } from 'react';
import { getPipelineStatus } from '../api';
import { PipelineStatus } from '../types';
import { CheckCircle, Clock, AlertCircle, FileText } from 'lucide-react';

interface PipelineStatusProps {
  testRunId: string;
  onRefresh?: () => void;
}

const PipelineStatusComponent: React.FC<PipelineStatusProps> = ({ testRunId, onRefresh }) => {
  const [status, setStatus] = useState<PipelineStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = async () => {
    if (!testRunId) return;
    
    try {
      setLoading(true);
      const statusData = await getPipelineStatus(testRunId);
      setStatus(statusData);
      setError(null);
    } catch (err) {
      setError('Failed to fetch pipeline status');
      console.error('Error fetching pipeline status:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 10000); // Refresh every 10 seconds
    return () => clearInterval(interval);
  }, [testRunId]);

  const getPhaseIcon = (phaseId: string, completed: boolean) => {
    if (completed) {
      return <CheckCircle className="w-5 h-5 text-green-500" />;
    }
    
    const phaseIcons = {
      exploration: <Clock className="w-5 h-5 text-blue-500" />,
      planning: <Clock className="w-5 h-5 text-yellow-500" />,
      execution: <Clock className="w-5 h-5 text-orange-500" />,
      reporting: <FileText className="w-5 h-5 text-purple-500" />
    };
    
    return phaseIcons[phaseId as keyof typeof phaseIcons] || <Clock className="w-5 h-5 text-gray-500" />;
  };

  const getPhaseColor = (phaseId: string, completed: boolean) => {
    if (completed) return 'border-green-500 bg-green-50';
    
    const phaseColors = {
      exploration: 'border-blue-500 bg-blue-50',
      planning: 'border-yellow-500 bg-yellow-50',
      execution: 'border-orange-500 bg-orange-50',
      reporting: 'border-purple-500 bg-purple-50'
    };
    
    return phaseColors[phaseId as keyof typeof phaseColors] || 'border-gray-300 bg-gray-50';
  };

  if (loading && !status) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Pipeline Status</h3>
        <div className="text-gray-500">Loading status...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center">
          <AlertCircle className="w-5 h-5 text-red-500 mr-2" />
          Pipeline Status
        </h3>
        <div className="text-red-600">{error}</div>
        <button 
          onClick={fetchStatus}
          className="mt-2 px-3 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!status) return null;

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Pipeline Status</h3>
        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-600">Progress: {status.overall_progress}</span>
          <button 
            onClick={() => { fetchStatus(); onRefresh && onRefresh(); }}
            className="text-sm px-2 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
          >
            Refresh
          </button>
        </div>
      </div>

      <div className="space-y-3">
        {Object.entries(status.phases).map(([phaseId, phaseInfo]) => (
          <div
            key={phaseId}
            className={`border rounded-lg p-4 ${getPhaseColor(phaseId, phaseInfo.completed)}`}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                {getPhaseIcon(phaseId, phaseInfo.completed)}
                <div>
                  <h4 className="font-medium capitalize">{phaseId}</h4>
                  <div className="text-sm text-gray-600">
                    {phaseInfo.completed ? `${phaseInfo.outputs.length} files generated` : 'Pending'}
                  </div>
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm text-gray-500">
                  {phaseInfo.outputs.length}/{phaseInfo.files_expected.length} files
                </div>
                {phaseInfo.completed && (
                  <div className="text-xs text-green-600 font-medium">Completed</div>
                )}
              </div>
            </div>
            
            {phaseInfo.outputs.length > 0 && (
              <div className="mt-2 pt-2 border-t border-gray-200">
                <div className="text-xs text-gray-600">
                  <span className="font-medium">Generated files:</span>
                </div>
                <div className="flex flex-wrap gap-1 mt-1">
                  {phaseInfo.outputs.map((file) => (
                    <span 
                      key={file}
                      className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded"
                    >
                      {file}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="mt-4 p-3 bg-gray-50 rounded-lg">
        <div className="text-sm text-gray-600">
          <span className="font-medium">Test Run ID:</span> {status.test_run_id}
        </div>
        <div className="text-sm text-gray-600 mt-1">
          <span className="font-medium">Status:</span> {status.is_complete ? 'Complete' : 'In Progress'}
        </div>
      </div>
    </div>
  );
};

export default PipelineStatusComponent;
