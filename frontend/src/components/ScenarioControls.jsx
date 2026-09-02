import React from 'react';
import { Flame, Shield, Square, Zap, Users, Database, AlertTriangle } from 'lucide-react';

export default function ScenarioControls({ currentMode, onSetMode }) {
  return (
    <div className="bg-slate-900/90 rounded-2xl border border-slate-800 p-5 backdrop-blur-md shadow-xl">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
        <div>
          <h2 className="text-base font-bold text-white flex items-center gap-2 font-mono">
            <Zap className="w-5 h-5 text-cyan-400" />
            Live Stage Presentation Triggers
          </h2>
          <p className="text-xs text-slate-400">
            Fire synthetic traffic patterns to demonstrate adaptive PoW throttling vs. non-DDoS I/O bottleneck diagnostics.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400 font-mono">Simulator State:</span>
          <span className={`text-xs font-bold font-mono px-2.5 py-1 rounded border ${
            currentMode === 'COMPLEXITY_ATTACK' ? 'bg-rose-500/20 text-rose-300 border-rose-500/40' :
            currentMode === 'BENIGN_SURGE' ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40' :
            currentMode === 'DOWNSTREAM_STALL' ? 'bg-amber-500/20 text-amber-300 border-amber-500/40' :
            'bg-slate-800 text-slate-300 border-slate-700'
          }`}>
            {currentMode}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-3.5">
        {/* Trigger 1: Legitimate Spike */}
        <button
          onClick={() => onSetMode('BENIGN_SURGE')}
          className={`flex flex-col text-left p-3.5 rounded-xl border transition-all duration-200 group ${
            currentMode === 'BENIGN_SURGE'
              ? 'bg-emerald-950/40 border-emerald-500 text-white ring-2 ring-emerald-500/20 shadow-lg shadow-emerald-500/10'
              : 'bg-slate-950/50 hover:bg-slate-800/80 border-slate-800 hover:border-emerald-500/50 text-slate-300'
          }`}
        >
          <div className="flex items-center justify-between w-full mb-1.5">
            <div className="flex items-center gap-1.5 font-semibold text-emerald-400 text-xs font-mono">
              <Users className="w-4 h-4" />
              <span>1. Benign Traffic Surge</span>
            </div>
            {currentMode === 'BENIGN_SURGE' && (
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
            )}
          </div>
          <p className="text-[11px] text-slate-400 leading-relaxed mb-2.5">
            Distributed organic surge (30+ RPS). Balanced endpoint load, sustainable CPU.
          </p>
          <div className="mt-auto flex items-center gap-1.5 text-[10px] font-mono text-emerald-400/90 font-medium">
            <Shield className="w-3 h-3" />
            <span>0 PoW (Zero friction)</span>
          </div>
        </button>

        {/* Trigger 2: Crypto-Exhaustion Attack */}
        <button
          onClick={() => onSetMode('COMPLEXITY_ATTACK')}
          className={`flex flex-col text-left p-3.5 rounded-xl border transition-all duration-200 group ${
            currentMode === 'COMPLEXITY_ATTACK'
              ? 'bg-rose-950/40 border-rose-500 text-white ring-2 ring-rose-500/20 shadow-lg shadow-rose-500/10'
              : 'bg-slate-950/50 hover:bg-slate-800/80 border-slate-800 hover:border-rose-500/50 text-slate-300'
          }`}
        >
          <div className="flex items-center justify-between w-full mb-1.5">
            <div className="flex items-center gap-1.5 font-semibold text-rose-400 text-xs font-mono">
              <Flame className="w-4 h-4" />
              <span>2. Complexity DoS Attack</span>
            </div>
            {currentMode === 'COMPLEXITY_ATTACK' && (
              <span className="w-2 h-2 rounded-full bg-rose-400 animate-ping" />
            )}
          </div>
          <p className="text-[11px] text-slate-400 leading-relaxed mb-2.5">
            Floods /verify-crypto (50+ RPS). Pegs CPU, latency degrades, countdown starts.
          </p>
          <div className="mt-auto flex items-center gap-1.5 text-[10px] font-mono text-rose-400/90 font-medium">
            <AlertTriangle className="w-3 h-3" />
            <span>Ramps Dynamic PoW</span>
          </div>
        </button>

        {/* Trigger 3: Downstream DB Stall */}
        <button
          onClick={() => onSetMode('DOWNSTREAM_STALL')}
          className={`flex flex-col text-left p-3.5 rounded-xl border transition-all duration-200 group ${
            currentMode === 'DOWNSTREAM_STALL'
              ? 'bg-amber-950/40 border-amber-500 text-white ring-2 ring-amber-500/20 shadow-lg shadow-amber-500/10'
              : 'bg-slate-950/50 hover:bg-slate-800/80 border-slate-800 hover:border-amber-500/50 text-slate-300'
          }`}
        >
          <div className="flex items-center justify-between w-full mb-1.5">
            <div className="flex items-center gap-1.5 font-semibold text-amber-400 text-xs font-mono">
              <Database className="w-4 h-4" />
              <span>3. Downstream DB Stall</span>
            </div>
            {currentMode === 'DOWNSTREAM_STALL' && (
              <span className="w-2 h-2 rounded-full bg-amber-400 animate-ping" />
            )}
          </div>
          <p className="text-[11px] text-slate-400 leading-relaxed mb-2.5">
            Simulates slow DB query/pool wait (280ms latency, flat 0% CPU).
          </p>
          <div className="mt-auto flex items-center gap-1.5 text-[10px] font-mono text-amber-400/90 font-medium">
            <Database className="w-3 h-3" />
            <span>PoW Suppressed + Advisory</span>
          </div>
        </button>

        {/* Baseline / Standby */}
        <button
          onClick={() => onSetMode('IDLE')}
          className={`flex flex-col text-left p-3.5 rounded-xl border transition-all duration-200 group ${
            currentMode === 'IDLE'
              ? 'bg-cyan-950/30 border-cyan-500/60 text-white'
              : 'bg-slate-950/50 hover:bg-slate-800/80 border-slate-800 text-slate-400'
          }`}
        >
          <div className="flex items-center justify-between w-full mb-1.5">
            <div className="flex items-center gap-1.5 font-semibold text-cyan-400 text-xs font-mono">
              <Square className="w-4 h-4" />
              <span>4. Baseline Traffic</span>
            </div>
            {currentMode === 'IDLE' && (
              <span className="w-2 h-2 rounded-full bg-cyan-400" />
            )}
          </div>
          <p className="text-[11px] text-slate-400 leading-relaxed mb-2.5">
            Normal background state (1-3 RPS). Demonstrates automatic PoW hysteresis decay.
          </p>
          <div className="mt-auto flex items-center gap-1.5 text-[10px] font-mono text-slate-400">
            <span>Standby SLA Monitoring</span>
          </div>
        </button>
      </div>
    </div>
  );
}
