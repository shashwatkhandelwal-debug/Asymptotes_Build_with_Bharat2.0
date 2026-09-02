import React from 'react';
import { Terminal } from 'lucide-react';

export default function RequestFeed({ recentLogs }) {
  const logs = recentLogs || [];

  return (
    <div className="bg-slate-900/90 rounded-2xl border border-slate-800 p-5 backdrop-blur-md shadow-xl">
      <div className="flex items-center justify-between mb-3 pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <Terminal className="w-4 h-4 text-cyan-400" />
          <h3 className="text-sm font-bold text-white font-mono">Live Request Stream & Gate Telemetry</h3>
        </div>
        <span className="text-[10px] font-mono text-slate-400">
          Showing last {logs.length} transactions
        </span>
      </div>

      <div className="space-y-1.5 max-h-52 overflow-y-auto font-mono text-xs pr-1">
        {logs.length === 0 ? (
          <div className="text-slate-500 text-center py-6 text-xs">Waiting for incoming requests...</div>
        ) : (
          logs.map((log) => {
            const isCrypto = log.endpoint.includes('verify-crypto');
            const isBlocked = log.status === 428 || log.status === 403;
            const isSolved = log.pow_solved;

            return (
              <div
                key={log.id}
                className={`flex items-center justify-between p-2 rounded-lg text-[11px] border transition-all ${
                  isBlocked
                    ? 'bg-rose-950/30 border-rose-500/40 text-rose-300'
                    : isSolved
                    ? 'bg-cyan-950/30 border-cyan-500/40 text-cyan-200'
                    : isCrypto
                    ? 'bg-amber-950/20 border-amber-500/30 text-amber-200'
                    : 'bg-slate-950/40 border-slate-800/80 text-slate-300'
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <span className={`w-1.5 h-1.5 rounded-full ${
                    isBlocked ? 'bg-rose-400 animate-ping' :
                    isSolved ? 'bg-cyan-400' :
                    isCrypto ? 'bg-amber-400' : 'bg-emerald-400'
                  }`} />
                  <span className="text-slate-400">{new Date(log.timestamp * 1000).toLocaleTimeString()}</span>
                  <span className="font-semibold text-slate-200">{log.endpoint}</span>
                  <span className="text-slate-500">({log.client_ip})</span>
                </div>

                <div className="flex items-center gap-3">
                  {log.pow_difficulty > 0 && (
                    <span className={`px-1.5 py-0.2 rounded text-[10px] ${
                      isSolved ? 'bg-cyan-500/20 text-cyan-300' : 'bg-rose-500/20 text-rose-300'
                    }`}>
                      PoW: {log.pow_difficulty}b ({isSolved ? 'SOLVED' : 'CHALLENGED'})
                    </span>
                  )}
                  <span className="text-slate-400">{log.latency_ms}ms (CPU: {log.cpu_time_ms}ms)</span>
                  <span className={`font-bold px-1.5 py-0.2 rounded text-[10px] ${
                    log.status === 200 ? 'bg-emerald-500/20 text-emerald-300' :
                    log.status === 428 ? 'bg-rose-500/20 text-rose-300' : 'bg-amber-500/20 text-amber-300'
                  }`}>
                    {log.status}
                  </span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
