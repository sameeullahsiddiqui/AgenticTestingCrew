import React, { useEffect, useState } from 'react';
import { listFiles } from '../api';
import { FolderOpen } from 'lucide-react';
import { config } from '../config';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

type Props = {
  runId: string;
  refreshSignal: number;
};

const OutputFiles = ({ runId, refreshSignal }: Props) => {
  const [files, setFiles] = useState<string[]>([]);
  const [previewContent, setPreviewContent] = useState<string>('');
  const [previewFile, setPreviewFile] = useState<string | null>(null);

  useEffect(() => {
    if (runId) {
      listFiles(runId).then(setFiles).catch(() => setFiles([]));
    }
  }, [runId, refreshSignal]);

  const handleFileClick = async (file: string) => {
    const ext = file.split('.').pop()?.toLowerCase();
    if (ext === 'json' || ext === 'md') {
      try {
        const res = await fetch(
          `${config.apiBase}/view?run_id=${runId}&filename=${encodeURIComponent(file)}`
        );
        const text = await res.text();
        setPreviewFile(file);
        setPreviewContent(text);
      } catch (err) {
        setPreviewFile(file);
        setPreviewContent('⚠️ Failed to load file.');
      }
    } else {
      // fallback to download
      window.open(
        `${config.apiBase}/download?run_id=${runId}&filename=${encodeURIComponent(file)}`,
        '_blank'
      );
    }
  };

  return (
    <div className="card bg-slate-800 bg-opacity-50 rounded-xl p-6 border border-slate-700 relative">
      <h3 className="text-xl font-semibold flex items-center gap-3 mb-4">
        <FolderOpen className="text-samee-yellow w-5 h-5" />
        Output Files
      </h3>

      <ul className="text-sm list-disc list-inside">
        {files.map((file) => (
          <li key={file}>
            <button
              onClick={() => handleFileClick(file)}
              className="px-3 py-1 rounded-full border text-sm bg-indigo-600 border-indigo-400 text-white"
            >
              {file}
            </button>
          </li>
        ))}
      </ul>

      {/* Modal for Preview */}
      {previewFile && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-70">
          <div className="bg-black rounded-xl shadow-lg max-w-3xl w-full max-h-[90vh] overflow-auto p-6">
            <div className="flex justify-between items-center mb-4 bg-black">
              <h2 className="text-lg font-bold bg-black">{previewFile}</h2>
              <button
                onClick={() => {
                  setPreviewFile(null);
                  setPreviewContent('');
                }}
                className="text-red-600 font-semibold"
              >
                ✕ Close
              </button>
            </div>
           <pre className="prose prose-slate max-w-none bg-black">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {previewContent}
              </ReactMarkdown>
      </pre>

          </div>
        </div>
      )}
    </div>
  );
};

export default OutputFiles;
