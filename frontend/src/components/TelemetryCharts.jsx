import React from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine
} from 'recharts';
import { Activity, Cpu } from 'lucide-react';

export default function TelemetryCharts({ history }) {
  const chartData = history && history.length > 0 ? history : [
    { time: '0s', latency: 15, cpu: 12, rps: 3, cryptoRps: 0.5 }
  ];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
      <div className="bg-slate-900/90 rounded-2xl border border-slate-800 p-5 backdrop-blur-md shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-cyan-400" />
            <h3 className="text-sm font-bold text-white font-mono">Response Latency vs SLA Limit (ms)</h3>
          </div>
          <span className="text-[11px] font-mono text-rose-400 bg-rose-500/10 border border-rose-500/30 px-2 py-0.5 rounded">
            SLA Threshold: 800 ms
          </span>
        </div>

        <div className="h-56 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="latencyGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#38bdf8" stopOpacity={0.4}/>
                  <stop offset="95%" stopColor="#38bdf8" stopOpacity={0.0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="time" stroke="#64748b" tick={{ fontSize: 10, fill: '#64748b' }} />
              <YAxis stroke="#64748b" domain={[0, 'auto']} tick={{ fontSize: 10, fill: '#64748b' }} />
              <Tooltip
                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                itemStyle={{ color: '#38bdf8' }}
              />
              <ReferenceLine y={800} stroke="#f43f5e" strokeDasharray="4 4" label={{ value: 'SLA Breach (800ms)', fill: '#f43f5e', fontSize: 10 }} />
              <Area type="monotone" dataKey="latency" name="Latency (ms)" stroke="#38bdf8" strokeWidth={2} fillOpacity={1} fill="url(#latencyGradient)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="bg-slate-900/90 rounded-2xl border border-slate-800 p-5 backdrop-blur-md shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Cpu className="w-4 h-4 text-amber-400" />
            <h3 className="text-sm font-bold text-white font-mono">System CPU Load (%) & Throughput</h3>
          </div>
          <span className="text-[11px] font-mono text-slate-400 bg-slate-800 px-2 py-0.5 rounded border border-slate-700">
            Real Hardware Telemetry
          </span>
        </div>

        <div className="h-56 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="time" stroke="#64748b" tick={{ fontSize: 10, fill: '#64748b' }} />
              <YAxis stroke="#64748b" domain={[0, 100]} tick={{ fontSize: 10, fill: '#64748b' }} />
              <Tooltip
                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
              />
              <ReferenceLine y={65} stroke="#f59e0b" strokeDasharray="3 3" label={{ value: 'Attack Threshold (65%)', fill: '#f59e0b', fontSize: 10 }} />
              <Line type="monotone" dataKey="cpu" name="CPU Utilization %" stroke="#f59e0b" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="rps" name="Requests / Sec" stroke="#a855f7" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
