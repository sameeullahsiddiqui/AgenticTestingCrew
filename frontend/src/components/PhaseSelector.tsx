import React, { useState, useEffect } from 'react';
import { fetchPhases } from '../api';
import { Phase } from '../types';

interface PhaseSelectorProps {
  selectedPhases: string[];
  onPhasesChange: (phases: string[]) => void;
}

const PhaseSelector: React.FC<PhaseSelectorProps> = ({ selectedPhases, onPhasesChange }) => {
  const [phases, setPhases] = useState<Phase[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadPhases = async () => {
      try {
        const phasesData = await fetchPhases();
        setPhases(phasesData);
      } catch (error) {
        console.error('Error loading phases:', error);
      } finally {
        setLoading(false);
      }
    };
    
    loadPhases();
  }, []);

  const handlePhaseToggle = (phaseId: string) => {
    if (selectedPhases.includes(phaseId)) {
      onPhasesChange(selectedPhases.filter(id => id !== phaseId));
    } else {
      onPhasesChange([...selectedPhases, phaseId]);
    }
  };

  const handleSelectAll = () => {
    if (selectedPhases.length === phases.length) {
      onPhasesChange([]);
    } else {
      onPhasesChange(phases.map(phase => phase.id));
    }
  };

  const getPhaseOrder = (phaseId: string): number => {
    const order = { exploration: 1, planning: 2, execution: 3, reporting: 4 };
    return order[phaseId as keyof typeof order] || 999;
  };

  const sortedPhases = [...phases].sort((a, b) => getPhaseOrder(a.id) - getPhaseOrder(b.id));

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Pipeline Phases</h3>
        <div className="text-gray-500">Loading phases...</div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Pipeline Phases</h3>
        <button
          onClick={handleSelectAll}
          className="text-sm px-3 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
        >
          {selectedPhases.length === phases.length ? 'Deselect All' : 'Select All'}
        </button>
      </div>
      
      <div className="space-y-3">
        {sortedPhases.map((phase) => (
          <div
            key={phase.id}
            className={`border rounded-lg p-4 cursor-pointer transition-colors ${
              selectedPhases.includes(phase.id)
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
            onClick={() => handlePhaseToggle(phase.id)}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    checked={selectedPhases.includes(phase.id)}
                    onChange={() => handlePhaseToggle(phase.id)}
                    className="mr-3 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <h4 className="font-medium text-gray-900">
                    {phase.name}
                    <span className="ml-2 text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded-full">
                      Phase {getPhaseOrder(phase.id)}
                    </span>
                  </h4>
                </div>
                <p className="text-sm text-gray-600 mt-1 ml-7">
                  {phase.description}
                </p>
                <div className="mt-2 ml-7">
                  <div className="text-xs text-gray-500">
                    <span className="font-medium">Outputs:</span> {phase.outputs.join(', ')}
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    <span className="font-medium">Agents:</span> {phase.agents.join(', ')}
                  </div>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
      
      {selectedPhases.length > 0 && (
        <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg">
          <div className="text-sm text-green-800">
            <span className="font-medium">Selected phases ({selectedPhases.length}):</span>
            <div className="mt-1">
              {selectedPhases
                .sort((a, b) => getPhaseOrder(a) - getPhaseOrder(b))
                .map(phaseId => {
                  const phase = phases.find(p => p.id === phaseId);
                  return phase ? phase.name : phaseId;
                })
                .join(' → ')
              }
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PhaseSelector;
