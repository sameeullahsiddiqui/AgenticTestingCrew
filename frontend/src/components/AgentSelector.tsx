// import React, { useEffect, useState } from 'react';
// import { fetchAgents } from '../api';
// import { Users } from 'lucide-react';

// type Agent = {
//   id: string;
//   role: string;
//   short_goal: string;
// };

// const AgentSelector = () => {
//   const [agents, setAgents] = useState<Agent[]>([]);

//   useEffect(() => {
//     fetchAgents().then(setAgents);
//   }, []);

//   return (
//     <div className="card bg-slate-800 bg-opacity-50 rounded-xl p-6 border border-slate-700">
//       <h3 className="text-xl font-semibold flex items-center gap-3 mb-4">
//         <Users className="text-samee-yellow w-5 h-5" />
//         Select Agents
//       </h3>

//       <div className="flex flex-col gap-3">
//         {agents.map(agent => (
//           <div key={agent.id} className="flex items-center gap-4 p-4 rounded-lg bg-slate-700 bg-opacity-50 hover:bg-slate-600 cursor-pointer">
//             <div className="w-5 h-5 border-2 border-slate-400 rounded-sm"></div>
//             <div className="text-xl">🤖</div>
//             <div className="flex-1">
//               <div className="font-medium">{agent.id}</div>
//               <div className="text-sm text-gray-400">{agent.short_goal}</div>
//             </div>
//           </div>
//         ))}
//       </div>
//     </div>
//   );
// };

// export default AgentSelector;