import React from 'react';
import { Play, Flame, Shield, Square, Zap, Users, AlertTriangle } from 'lucide-react';

export default function ScenarioControls({ currentMode, onSetMode }) {
  return (
    <div className="bg-slate-900/90 rounded-2xl border border-slate-800 p-5 backdrop-blur-md shadow-xl">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
        <div>
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <Zap className="w-5 h-5 text-cyan-400" />
            Live Stage Presentation Triggers
          </h2>
          <p className="text-xs text-slate-400">
            Fire synthetic traffic patterns to demonstrate adaptive classification and dynamic PoW throttling.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400 font-mono">Current Simulator Mode:</span>
          <span className={`text-xs font-bold font-mono px-2.5 py-1 rounded border ${
            currentMode === 'COMPLEXITY_ATTACK' ? 'bg-rose-500/20 text-rose-300 border-rose-500/40' :
            currentMode === 'BENIGN_SURGE' ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40' :
            'bg-slate-800 text-slate-300 border-slate-700'
          }`}>
            {currentMode}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5">
        {/* Trigger 1: Legitimate Spike */}
        <button
          onClick={() => onSetMode('BENIGN_SURGE')}
          className={`flex flex-col text-left p-4 rounded-xl border transition-all duration-200 group ${
            currentMode === 'BENIGN_SURGE'
              ? 'bg-emerald-950/40 border-emerald-500 text-white ring-2 ring-emerald-500/20 shadow-lg shadow-emerald-500/10'
              : 'bg-slate-950/50 hover:bg-slate-800/80 border-slate-800 hover:border-emerald-500/50 text-slate-300'
          }`}
        >
          <div className="flex items-center justify-between w-full mb-2">
            <div className="flex items-center gap-2 font-semibold text-emerald-400 text-sm">
              <Users className="w-4 h-4" />
              <span>1. Legitimate Traffic Spike</span>
            </div>
            {currentMode === 'BENIGN_SURGE' && (
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping" />
            )}
          </div>
          <p className="text-xs text-slate-400 leading-relaxed mb-3">
            Simulates distributed organic surge (25-35 RPS). High volume across light endpoints, low crypto concentration.
          </p>
          <div className="mt-auto flex items-center gap-2 text-[11px] font-mono text-emerald-400/90 font-medium">
            <Shield className="w-3.5 h-3.5" />
            <span>Result: 0 PoW Challenges (No user friction)</span>
          </div>
        </button>

        {/* Trigger 2: Crypto-Exhaustion Attack */}
        <button
          onClick={() => onSetMode('COMPLEXITY_ATTACK')}
          className={`flex flex-col text-left p-4 rounded-xl border transition-all duration-200 group ${
            currentMode === 'COMPLEXITY_ATTACK'
              ? 'bg-rose-950/40 border-rose-500 text-white ring-2 ring-rose-500/20 shadow-lg shadow-rose-500/10'
              : 'bg-slate-950/50 hover:bg-slate-800/80 border-slate-800 hover:border-rose-500/50 text-slate-300'
          }`}
        >
          <div className="flex items-center justify-between w-full mb-2">
            <div className="flex items-center gap-2 font-semibold text-rose-400 text-sm">
              <Flame className="w-4 h-4" />
              <span>2. Crypto-Exhaustion Attack</span>
            </div>
            {currentMode === 'COMPLEXITY_ATTACK' && (
              <span className="w-2.5 h-2.5 rounded-full bg-rose-400 animate-ping" />
            )}
          </div>
          <p className="text-xs text-slate-400 leading-relaxed mb-3">
            Floods heavy PBKDF2 cryptographic verification endpoint (50+ RPS). Pegs CPU, degrades latency, triggers countdown.
          </p>
          <div className="mt-auto flex items-center gap-2 text-[11px] font-mono text-rose-400/90 font-medium">
            <AlertTriangle className="w-3.5 h-3.5" />
            <span>Result: Ramps Dynamic PoW & Throttles Attackers</span>
          </div>
        </button>

        {/* Baseline / Stop */}
        <button
          onClick={() => onSetMode('IDLE')}
          className={`flex flex-col text-left p-4 rounded-xl border transition-all duration-200 group ${
            currentMode === 'IDLE'
              ? 'bg-cyan-950/30 border-cyan-500/60 text-white'
              : 'bg-slate-950/50 hover:bg-slate-800/80 border-slate-800 text-slate-400'
          }`}
        >
          <div className="flex items-center justify-between w-full mb-2">
            <div className="flex items-center gap-2 font-semibold text-cyan-400 text-sm">
              <Square className="w-4 h-4" />
              <span>Baseline Traffic / Standby</span>
            </div>
            {currentMode === 'IDLE' && (
              <span className="w-2.5 h-2.5 rounded-full bg-cyan-400" />
            )}
          </div>
          <p className="text-xs text-slate-400 leading-relaxed mb-3">
            Returns to normal background state (1-3 RPS). Demonstrates automatic PoW difficulty decay (hysteresis) back to 0.
          </p>
          <div className="mt-auto flex items-center gap-2 text-[11px] font-mono text-slate-400">
            <span>Standby state monitoring SLA</span>
          </div>
        </button>
      </div>
    </div>
  );
}
