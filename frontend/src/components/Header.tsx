import React from 'react';

type HeaderProps = {
  status: 'Online' | 'Offline';
};

const Header = ({ status }: HeaderProps) => {
  const isOnline = status === 'Online';

  return (
    <header className="border-b bg-slate-800 bg-opacity-50 backdrop-blur text-white">
      <div className="p-6 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-indigo-400 to-purple-500 text-transparent bg-clip-text">
            AI Testing Team
          </h1>
          <p className="text-gray-400">AI Enabled Automated Testing</p>
        </div>
        <div
          className={`flex items-center gap-2 px-3 py-1 rounded-full text-sm ${
            isOnline
              ? 'bg-emerald-500/10 text-emerald-400'
              : 'bg-red-500/10 text-red-400'
          }`}
        >
          <div
            className={`w-2 h-2 rounded-full animate-pulse ${
              isOnline ? 'bg-emerald-400' : 'bg-red-400'
            }`}
          ></div>
          System {status}
        </div>
      </div>
    </header>
  );
};

export default Header;
