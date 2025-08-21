import React, { useEffect, useState, useRef } from 'react';
import { AnsiUp } from 'ansi_up';
import { marked } from 'marked';

type LogEntry = string | { message: string; source: string };

const LiveLogs = ({ logs }: { logs: LogEntry[] }) => {
  const [ansiUp, setAnsiUp] = useState<AnsiUp | null>(null);
  const logEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setAnsiUp(new AnsiUp());
  }, []);

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  const getLogClass = (message: string) => {
    if (message.includes('ERROR') || message.includes('error')) return 'text-red-400';
    if (message.includes('SUCCESS')) return 'text-emerald-400';
    if (message.includes('INFO')) return 'text-sky-400';
    return 'text-samee-yellow';
  };

  if (!ansiUp) return <div className="text-sm text-gray-400">Loading logs...</div>;

  return (
    <div className="max-h-[500px] overflow-y-auto p-2 bg-black text-white font-mono text-sm space-y-1">
      {logs.map((log, i) => 
      {      
        try {
          if (typeof log === 'string') {
                const maybeJson = JSON.parse(log);

                if (maybeJson && maybeJson.source && maybeJson.message) {
                    const message = typeof maybeJson.message === 'object'
                      ? JSON.stringify(maybeJson.message, null, 2)
                      : maybeJson.message;
                    return (
                      <div key={i} className={getLogClass(message)}>
                        [{maybeJson.source}] {maybeJson.message}
                      </div>
                    );
                } else {
                    return (
                      <div key={i} className={getLogClass(log)}>
                        {log}
                      </div>
                    );
                  }
            } else {
                    const message = typeof log.message === 'object'
                      ? log.message['message']
                      : log.message;

                    const isMarkdown = message.includes('##') || message.includes('- ') || message.includes('**');
                    const html = isMarkdown ? marked.parse(message) : ansiUp.ansi_to_html(message);
                    

                    return (
                                <pre 
                                  key={`log-${i}`}
                                  className={getLogClass(message)}
                                  dangerouslySetInnerHTML={{ __html: html }}
                                />
                          );
            }
          } catch (err) {
            // Failed to parse JSON, just print it
            return (
              <div key={i} className="text-samee-yellow">
                {String(log)}
              </div>
            );
          }

      })}
      <div ref={logEndRef} />
    </div>
  );
};

export default LiveLogs;
