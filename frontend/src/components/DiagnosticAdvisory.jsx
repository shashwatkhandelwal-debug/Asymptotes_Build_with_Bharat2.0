import React from 'react';
import { ShieldAlert, ShieldCheck, Database, Wrench, Info } from 'lucide-react';

export default function DiagnosticAdvisory({ classification }) {
  const advisory = classification?.advisory;

  if (!advisory) {
    return null;
  }

  const isWarning = advisory.severity === 'WARNING';
  const isCritical = advisory.severity === 'CRITICAL';

  return (
    <div className={`rounded-2xl border p-5 backdrop-blur-md transition-all duration-300 ${
      isCritical ? 'bg-rose-950/40 border-rose-500/70 glow-rose' :
      isWarning ? 'bg-amber-950/40 border-amber-500/70 glow-amber' :
      'bg-emerald-950/30 border-emerald-500/50 glow-emerald'
    }`}>
      <div className="flex items-start justify-between gap-4 mb-3">
        <div className="flex items-center gap-2.5">
          {isCritical ? (
            <ShieldAlert className="w-5 h-5 text-rose-400 flex-shrink-0 animate-pulse" />
          ) : isWarning ? (
            <Database className="w-5 h-5 text-amber-400 flex-shrink-0 animate-bounce" />
          ) : (
            <ShieldCheck className="w-5 h-5 text-emerald-400 flex-shrink-0" />
          )}
          <div>
            <h3 className="text-sm font-bold text-white font-mono flex items-center gap-2">
              <span>{advisory.title}</span>
              <span className={`text-[10px] px-2 py-0.5 rounded font-mono font-bold ${
                isCritical ? 'bg-rose-500/30 text-rose-200' :
                isWarning ? 'bg-amber-500/30 text-amber-200' :
                'bg-emerald-500/30 text-emerald-200'
              }`}>
                {advisory.code}
              </span>
            </h3>
            <p className="text-xs text-slate-300 mt-0.5">
              {advisory.root_cause}
            </p>
          </div>
        </div>

        <span className={`text-[11px] font-mono px-2.5 py-1 rounded font-bold uppercase ${
          isCritical ? 'bg-rose-500 text-white' :
          isWarning ? 'bg-amber-500 text-slate-950' :
          'bg-emerald-500 text-white'
        }`}>
          {advisory.severity}
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-3 pt-3 border-t border-slate-800/80 text-xs font-mono">
        <div className="bg-slate-950/60 p-2.5 rounded-xl border border-slate-800/80">
          <div className="text-slate-400 text-[10px] uppercase font-bold flex items-center gap-1.5 mb-1">
            <Info className="w-3.5 h-3.5 text-cyan-400" />
            <span>Autonomous System Action</span>
          </div>
          <p className="text-slate-200 leading-snug">
            {advisory.defense_action}
          </p>
        </div>

        <div className="bg-slate-950/60 p-2.5 rounded-xl border border-slate-800/80">
          <div className="text-slate-400 text-[10px] uppercase font-bold flex items-center gap-1.5 mb-1">
            <Wrench className="w-3.5 h-3.5 text-amber-400" />
            <span>Recommended Engineering Remediation</span>
          </div>
          <p className="text-slate-200 leading-snug">
            {advisory.remediation}
          </p>
        </div>
      </div>
    </div>
  );
}
