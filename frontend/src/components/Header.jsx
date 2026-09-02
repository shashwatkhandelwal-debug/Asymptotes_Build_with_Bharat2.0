import React from 'react';
import { ShieldCheck, ShieldAlert, Shield, Activity, RefreshCw, Cpu, Radio } from 'lucide-react';

export default function Header({ isConnected, classification, powState, onResetDemo }) {
  const getBadge = () => {
    const type = classification?.classification || 'NORMAL';
    switch (type) {
      case 'COMPLEXITY_ATTACK':
        return {
          label: 'CRITICAL THREAT: COMPLEXITY ATTACK',
          color: 'bg-rose-500/20 text-rose-400 border-rose-500/50 glow-rose animate-pulse',
          icon: <ShieldAlert className="w-5 h-5" />
        };
      case 'BENIGN_SURGE':
        return {
          label: 'BENIGN TRAFFIC SURGE (LEGITIMATE)',
          color: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/50 glow-emerald',
          icon: <ShieldCheck className="w-5 h-5" />
        };
      case 'DOWNSTREAM_STALL':
        return {
          label: 'DOWNSTREAM I/O BOTTLENECK',
          color: 'bg-amber-500/20 text-amber-400 border-amber-500/50 glow-amber',
          icon: <Activity className="w-5 h-5" />
        };
      default:
        return {
          label: 'DEFENSE ARMED & MONITORING',
          color: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30',
          icon: <Shield className="w-5 h-5" />
        };
    }
  };

  const badge = getBadge();

  return (
    <header className="border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-600 to-blue-500 flex items-center justify-center shadow-lg shadow-cyan-500/20">
            <Cpu className="w-6 h-6 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold tracking-tight text-white font-mono">
                ASYMPTOTE<span className="text-cyan-400">.PoW</span>
              </h1>
              <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 font-mono border border-slate-700">
                v2.0 Stage Demo
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Adaptive Proof-of-Work Defense Against Algorithmic Complexity Attacks
            </p>
          </div>
        </div>

        {/* Status Center & Controls */}
        <div className="flex items-center flex-wrap gap-3">
          {/* Classification Badge */}
          <div className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg border text-xs font-semibold font-mono transition-all duration-300 ${badge.color}`}>
            {badge.icon}
            <span>{badge.label}</span>
          </div>

          {/* Connection Indicator */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-300 font-mono">
            <Radio className={`w-3.5 h-3.5 ${isConnected ? 'text-emerald-400 animate-pulse' : 'text-rose-400'}`} />
            <span>{isConnected ? 'Telemetry 60fps' : 'Reconnecting...'}</span>
          </div>

          {/* Demo Reset Button */}
          <button
            onClick={onResetDemo}
            title="Reset simulated traffic and demo ledger state"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 text-xs font-medium transition-all"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Reset Demo</span>
          </button>
        </div>
      </div>
    </header>
  );
}
