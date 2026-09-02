import React, { useState, useEffect, useRef } from 'react';
import Header from './components/Header';
import ScenarioControls from './components/ScenarioControls';
import HeroDefenseMetrics from './components/HeroDefenseMetrics';
import DiagnosticAdvisory from './components/DiagnosticAdvisory';
import TelemetryCharts from './components/TelemetryCharts';
import LedgerExplorer from './components/LedgerExplorer';
import RequestFeed from './components/RequestFeed';

export default function App() {
  const [isConnected, setIsConnected] = useState(false);
  const [telemetryState, setTelemetryState] = useState({
    metrics: {
      rps: 0,
      crypto_rps: 0,
      benign_rps: 0,
      crypto_concentration: 0,
      mean_latency_ms: 10,
      system_cpu_percent: 15,
      latency_slope: 0,
      recent_logs: []
    },
    classification: {
      classification: 'NORMAL',
      confidence: 0.9,
      rationale: 'System operating within normal baseline envelope.',
      advisory: null
    },
    time_to_failure: {
      is_degrading: false,
      seconds_to_failure: null,
      urgency_score: 0.0,
      status_label: 'STABLE',
      explanation: 'Traffic is operating safely within SLA limits.'
    },
    pow_state: {
      difficulty_bits: 0,
      expected_hashes: 0,
      is_active: false
    },
    ledger_status: {
      is_valid: true,
      total_blocks: 1,
      message: 'Ledger intact.'
    },
    simulator: {
      mode: 'IDLE',
      is_running: true
    }
  });

  const [history, setHistory] = useState([]);
  const wsRef = useRef(null);

  useEffect(() => {
    let reconnectTimeout = null;

    const connect = () => {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws/telemetry`;

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (payload.type === 'TELEMETRY_UPDATE') {
            setTelemetryState(payload);

            const nowTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
            setHistory((prev) => {
              const next = [
                ...prev.slice(-25),
                {
                  time: nowTime,
                  latency: payload.metrics.mean_latency_ms || 1,
                  cpu: payload.metrics.system_cpu_percent || 0,
                  rps: payload.metrics.rps || 0,
                  cryptoRps: payload.metrics.crypto_rps || 0
                }
              ];
              return next;
            });
          }
        } catch (e) {
          console.error(e);
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        reconnectTimeout = setTimeout(connect, 2000);
      };

      ws.onerror = () => {
        setIsConnected(false);
        ws.close();
      };
    };

    connect();

    return () => {
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  const handleSetMode = async (mode) => {
    try {
      await fetch('/api/simulator/mode', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode })
      });
    } catch (e) {
      console.error(e);
    }
  };

  const handleMasterReset = async () => {
    try {
      await fetch('/api/simulator/reset', { method: 'POST' });
      setHistory([]);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="min-h-screen bg-[#070a10] text-slate-100 flex flex-col selection:bg-cyan-500 selection:text-white pb-12">
      <Header
        isConnected={isConnected}
        classification={telemetryState.classification}
        powState={telemetryState.pow_state}
        onResetDemo={handleMasterReset}
      />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 flex-1 flex flex-col gap-6 w-full">
        <ScenarioControls
          currentMode={telemetryState.simulator?.mode || 'IDLE'}
          onSetMode={handleSetMode}
        />

        <DiagnosticAdvisory classification={telemetryState.classification} />

        <HeroDefenseMetrics
          metrics={telemetryState.metrics}
          classification={telemetryState.classification}
          timeToFailure={telemetryState.time_to_failure}
          powState={telemetryState.pow_state}
        />

        <TelemetryCharts history={history} />

        <LedgerExplorer ledgerStatus={telemetryState.ledger_status} />

        <RequestFeed recentLogs={telemetryState.metrics?.recent_logs} />
      </main>

      <footer className="border-t border-slate-800/80 bg-slate-950/60 py-4 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-slate-500 font-mono">
          <div>
            Adaptive Proof-of-Work Defense & Diagnostic Platform • Build with Bharat 2.0
          </div>
          <div>
            Heuristic Telemetry Classifier • Hashcash SHA-256 Web Worker • Local Hash-Chained Ledger
          </div>
        </div>
      </footer>
    </div>
  );
}
