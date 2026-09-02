import React from 'react';
import { Timer, Gauge, BrainCircuit, ShieldAlert, CheckCircle2, TrendingUp, AlertOctagon } from 'lucide-react';

export default function HeroDefenseMetrics({ metrics, classification, timeToFailure, powState }) {
  const ttf = timeToFailure || {};
  const pow = powState || {};
  const classData = classification || {};
  const diffBits = pow.difficulty_bits || 0;
  const isAttack = classData.classification === 'COMPLEXITY_ATTACK';
  const isSurge = classData.classification === 'BENIGN_SURGE';

  // Format countdown
  const secondsLeft = ttf.seconds_to_failure;
  const isDegrading = ttf.is_degrading;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
      {/* 1. Time to SLA Failure Countdown */}
      <div className={`rounded-2xl border p-5 backdrop-blur-md relative overflow-hidden transition-all duration-300 ${
        isDegrading && secondsLeft < 10
          ? 'bg-rose-950/40 border-rose-500/60 shadow-xl shadow-rose-950/50 glow-rose'
          : isDegrading
          ? 'bg-amber-950/30 border-amber-500/50 glow-amber'
          : 'bg-slate-900/90 border-slate-800 shadow-xl'
      }`}>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2 text-slate-300 text-xs font-semibold uppercase tracking-wider">
            <Timer className={`w-4 h-4 ${isDegrading ? 'text-rose-400 animate-spin' : 'text-cyan-400'}`} />
            <span>Time-to-SLA Failure (Regression)</span>
          </div>
          <span className={`text-[11px] font-mono px-2 py-0.5 rounded-full font-bold border ${
            ttf.status_label === 'CRITICAL' ? 'bg-rose-500/20 text-rose-300 border-rose-500/40 animate-pulse' :
            ttf.status_label === 'WARNING' ? 'bg-amber-500/20 text-amber-300 border-amber-500/40' :
            'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
          }`}>
            {ttf.status_label || 'STABLE'}
          </span>
        </div>

        <div className="flex items-baseline gap-2 mb-2">
          {isDegrading && secondsLeft !== null ? (
            <>
              <span className={`text-4xl font-extrabold font-mono tracking-tight ${
                secondsLeft < 5 ? 'text-rose-400 animate-pulse' : 'text-amber-400'
              }`}>
                {secondsLeft.toFixed(1)}
              </span>
              <span className="text-sm font-semibold text-slate-400 font-mono">seconds</span>
            </>
          ) : (
            <div className="flex items-center gap-2 text-emerald-400">
              <CheckCircle2 className="w-8 h-8" />
              <div>
                <div className="text-2xl font-bold font-mono">SLA SAFE</div>
                <div className="text-xs text-emerald-500/80 font-mono">Latency within limits</div>
              </div>
            </div>
          )}
        </div>

        <p className="text-xs text-slate-400 leading-snug mb-3">
          {ttf.explanation || 'Real-time linear regression over latency degradation slope.'}
        </p>

        {/* Urgency Progress Bar */}
        <div className="w-full bg-slate-950 rounded-full h-2 overflow-hidden border border-slate-800">
          <div
            className={`h-full transition-all duration-300 ${
              (ttf.urgency_score || 0) > 0.6 ? 'bg-gradient-to-r from-amber-500 to-rose-500' :
              (ttf.urgency_score || 0) > 0.2 ? 'bg-gradient-to-r from-cyan-500 to-amber-500' :
              'bg-emerald-500'
            }`}
            style={{ width: `${Math.min(100, (ttf.urgency_score || 0) * 100)}%` }}
          />
        </div>
        <div className="flex justify-between text-[10px] font-mono text-slate-500 mt-1">
          <span>Urgency Score: {Math.round((ttf.urgency_score || 0) * 100)}%</span>
          <span>SLA Threshold: 800ms</span>
        </div>
      </div>

      {/* 2. Dynamic PoW Difficulty Dial */}
      <div className={`rounded-2xl border p-5 backdrop-blur-md relative overflow-hidden transition-all duration-300 ${
        diffBits > 0
          ? 'bg-cyan-950/30 border-cyan-500/50 shadow-xl shadow-cyan-950/40 glow-cyan'
          : 'bg-slate-900/90 border-slate-800 shadow-xl'
      }`}>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2 text-slate-300 text-xs font-semibold uppercase tracking-wider">
            <Gauge className="w-4 h-4 text-cyan-400" />
            <span>Dynamic PoW Difficulty Dial</span>
          </div>
          <span className={`text-[11px] font-mono px-2 py-0.5 rounded-full font-bold border ${
            diffBits > 0
              ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40 animate-pulse'
              : 'bg-slate-800 text-slate-400 border-slate-700'
          }`}>
            {diffBits > 0 ? 'CHALLENGE ACTIVE' : 'POW INACTIVE'}
          </span>
        </div>

        <div className="flex items-baseline gap-2 mb-2">
          <span className="text-4xl font-extrabold font-mono tracking-tight text-white">
            {diffBits}
          </span>
          <span className="text-sm font-semibold text-cyan-400 font-mono">leading bits</span>
          <span className="text-xs text-slate-400 font-mono ml-auto">
            ~{pow.expected_hashes?.toLocaleString() || 0} hashes/req
          </span>
        </div>

        <p className="text-xs text-slate-400 leading-snug mb-3">
          {diffBits > 0
            ? `Throttling attackers: client must compute SHA-256 Hashcash proof with ${diffBits} zero bits.`
            : 'PoW disabled. Legitimate and surge traffic passes through with zero client computing delay.'}
        </p>

        {/* Difficulty Scale Meter */}
        <div className="grid grid-cols-5 gap-1.5 mb-1.5">
          {[0, 8, 10, 12, 16].map((level, idx) => (
            <div
              key={level}
              className={`h-2 rounded transition-all duration-300 ${
                diffBits >= level && (level > 0 || diffBits === 0)
                  ? level === 0 ? 'bg-slate-700' :
                    level <= 10 ? 'bg-cyan-500' :
                    level <= 14 ? 'bg-amber-500' : 'bg-rose-500'
                  : 'bg-slate-800/80'
              }`}
            />
          ))}
        </div>
        <div className="flex justify-between text-[10px] font-mono text-slate-500">
          <span>0 bits (Off)</span>
          <span>8 bits (Mild)</span>
          <span>12 bits (Mod)</span>
          <span>16 bits (Max)</span>
        </div>
      </div>

      {/* 3. Real-Time Classifier Diagnostics */}
      <div className="bg-slate-900/90 rounded-2xl border border-slate-800 p-5 backdrop-blur-md shadow-xl flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2 text-slate-300 text-xs font-semibold uppercase tracking-wider">
              <BrainCircuit className="w-4 h-4 text-cyan-400" />
              <span>Telemetry Classifier Engine</span>
            </div>
            <span className="text-[10px] font-mono text-slate-400 bg-slate-800 px-2 py-0.5 rounded border border-slate-700">
              Rule-Based Heuristic
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2.5 mb-3 font-mono text-xs">
            <div className="bg-slate-950/60 p-2 rounded-lg border border-slate-800/80">
              <div className="text-slate-400 text-[10px]">CPU STRESS</div>
              <div className={`font-bold text-sm ${metrics.system_cpu_percent > 60 ? 'text-rose-400' : 'text-slate-200'}`}>
                {metrics.system_cpu_percent || 0}%
              </div>
            </div>

            <div className="bg-slate-950/60 p-2 rounded-lg border border-slate-800/80">
              <div className="text-slate-400 text-[10px]">CRYPTO CONCENTRATION</div>
              <div className={`font-bold text-sm ${metrics.crypto_concentration > 0.6 ? 'text-rose-400' : 'text-slate-200'}`}>
                {Math.round((metrics.crypto_concentration || 0) * 100)}%
              </div>
            </div>

            <div className="bg-slate-950/60 p-2 rounded-lg border border-slate-800/80">
              <div className="text-slate-400 text-[10px]">LATENCY SLOPE</div>
              <div className={`font-bold text-sm ${metrics.latency_slope > 10 ? 'text-rose-400' : 'text-slate-200'}`}>
                +{metrics.latency_slope || 0} ms/s
              </div>
            </div>

            <div className="bg-slate-950/60 p-2 rounded-lg border border-slate-800/80">
              <div className="text-slate-400 text-[10px]">AGGREGATE RPS</div>
              <div className="font-bold text-sm text-cyan-400">
                {metrics.rps || 0} req/s
              </div>
            </div>
          </div>
        </div>

        <p className="text-xs text-slate-400 border-t border-slate-800/80 pt-2.5 leading-snug">
          <strong className="text-slate-300">Diagnosis:</strong> {classData.rationale || 'Evaluating live traffic vectors.'}
        </p>
      </div>
    </div>
  );
}
