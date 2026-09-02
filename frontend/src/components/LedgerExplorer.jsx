import React, { useState, useEffect } from 'react';
import { Blocks, Link2, ShieldCheck, ShieldAlert, CheckCircle, AlertTriangle, RefreshCw, Lock, Bug } from 'lucide-react';

export default function LedgerExplorer({ ledgerStatus }) {
  const [blocks, setBlocks] = useState([]);
  const [verificationReport, setVerificationReport] = useState(null);
  const [isVerifying, setIsVerifying] = useState(false);
  const [tamperTargetIndex, setTamperTargetIndex] = useState(1);
  const [tamperMsg, setTamperMsg] = useState(null);

  const fetchBlocks = async () => {
    try {
      const res = await fetch('/api/ledger/blocks?limit=20');
      const data = await res.json();
      setBlocks(data.blocks || []);
      setVerificationReport(data.verification || null);
    } catch (e) {
      console.error('Failed to fetch ledger:', e);
    }
  };

  useEffect(() => {
    fetchBlocks();
    const interval = setInterval(fetchBlocks, 1500);
    return () => clearInterval(interval);
  }, []);

  const handleVerify = async () => {
    setIsVerifying(true);
    try {
      const res = await fetch('/api/ledger/verify');
      const data = await res.json();
      setVerificationReport(data);
    } catch (e) {
      console.error('Verification error:', e);
    } finally {
      setIsVerifying(false);
    }
  };

  const handleSimulateTamper = async () => {
    try {
      const target = blocks.find(b => b.block_index > 0)?.block_index || 1;
      const res = await fetch('/api/ledger/tamper', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ block_index: target, new_status: 'UNAUTHORIZED_ALTERATION' })
      });
      const data = await res.json();
      setTamperMsg(data.message);
      await fetchBlocks();
      await handleVerify();
    } catch (e) {
      console.error('Tamper error:', e);
    }
  };

  const handleResetDemoState = async () => {
    try {
      await fetch('/api/ledger/reset', { method: 'POST' });
      setTamperMsg(null);
      await fetchBlocks();
      await handleVerify();
    } catch (e) {
      console.error('Reset error:', e);
    }
  };

  const isChainValid = verificationReport?.is_valid !== false;

  return (
    <div className="bg-slate-900/90 rounded-2xl border border-slate-800 p-5 backdrop-blur-md shadow-xl">
      {/* Header & Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <Blocks className="w-5 h-5 text-cyan-400" />
            <h2 className="text-base font-bold text-white font-mono">
              Tamper-Evident Hash-Chained Audit Ledger
            </h2>
          </div>
          <p className="text-xs text-slate-400">
            Every issued challenge, solution, and dropped request is linked via sequential SHA-256 block hashes.
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center flex-wrap gap-2.5">
          <button
            onClick={handleVerify}
            disabled={isVerifying}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-mono text-xs font-semibold shadow-lg shadow-cyan-600/20 transition-all"
          >
            <ShieldCheck className="w-4 h-4" />
            <span>{isVerifying ? 'Verifying Chain...' : 'Verify Chain Integrity'}</span>
          </button>

          <button
            onClick={handleSimulateTamper}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-rose-600/80 hover:bg-rose-600 text-white font-mono text-xs font-semibold shadow-lg shadow-rose-600/20 transition-all"
            title="Simulate modifying a database record to prove cryptographic tamper-detection live on stage"
          >
            <Bug className="w-4 h-4" />
            <span>Simulate Block Tamper</span>
          </button>

          <button
            onClick={handleResetDemoState}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-mono text-xs font-medium border border-slate-700 transition-all"
            title="Reset local demo environment to genesis state"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Demo Reset</span>
          </button>
        </div>
      </div>

      {/* Verification Status Banner */}
      <div className="my-4">
        {isChainValid ? (
          <div className="flex items-center justify-between p-3.5 rounded-xl bg-emerald-950/40 border border-emerald-500/50 text-emerald-300 text-xs font-mono">
            <div className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-emerald-400 flex-shrink-0" />
              <span>
                <strong>CRYPTOGRAPHIC INTEGRITY VERIFIED:</strong> All {blocks.length} blocks hash-linked. No unauthorized modifications.
              </span>
            </div>
            <span className="text-[11px] px-2 py-0.5 rounded bg-emerald-500/20 font-bold">
              CHAIN VALID
            </span>
          </div>
        ) : (
          <div className="flex flex-col sm:flex-row sm:items-center justify-between p-3.5 rounded-xl bg-rose-950/60 border border-rose-500 text-rose-200 text-xs font-mono glow-rose animate-pulse gap-2">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-rose-400 flex-shrink-0" />
              <div>
                <strong className="text-rose-400">TAMPER ATTACK DETECTED:</strong> {verificationReport?.message}
                <div className="text-[11px] text-rose-300">
                  Target: Block #{verificationReport?.tampered_block_index} failed SHA-256 payload validation!
                </div>
              </div>
            </div>
            <span className="text-[11px] px-2.5 py-1 rounded bg-rose-500 text-white font-bold self-start sm:self-auto">
              INTEGRITY BREACH
            </span>
          </div>
        )}
      </div>

      {/* Block Stream Table */}
      <div className="overflow-x-auto rounded-xl border border-slate-800">
        <table className="w-full text-left font-mono text-xs">
          <thead className="bg-slate-950/80 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
            <tr>
              <th className="py-2.5 px-3">Block #</th>
              <th className="py-2.5 px-3">Timestamp</th>
              <th className="py-2.5 px-3">Client Fingerprint / IP</th>
              <th className="py-2.5 px-3">Difficulty</th>
              <th className="py-2.5 px-3">PoW Status</th>
              <th className="py-2.5 px-3">Previous Hash</th>
              <th className="py-2.5 px-3">Block Hash (SHA-256)</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 bg-slate-950/40">
            {blocks.map((block) => {
              const isTampered = !isChainValid && block.block_index === verificationReport?.tampered_block_index;
              return (
                <tr
                  key={block.block_index}
                  className={`hover:bg-slate-800/40 transition-colors ${
                    isTampered ? 'bg-rose-950/40 border-l-4 border-rose-500 font-bold' : ''
                  }`}
                >
                  <td className="py-2 px-3 text-cyan-400 font-bold">
                    #{block.block_index}
                  </td>
                  <td className="py-2 px-3 text-slate-400">
                    {new Date(block.timestamp * 1000).toLocaleTimeString()}
                  </td>
                  <td className="py-2 px-3 text-slate-300">
                    {block.client_ip}
                  </td>
                  <td className="py-2 px-3">
                    <span className={`px-2 py-0.5 rounded text-[11px] ${
                      block.difficulty_bits > 0
                        ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                        : 'bg-slate-800 text-slate-400'
                    }`}>
                      {block.difficulty_bits} bits
                    </span>
                  </td>
                  <td className="py-2 px-3">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      block.status === 'SOLVED' ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40' :
                      block.status === 'GENESIS' ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40' :
                      block.status === 'UNAUTHORIZED_ALTERATION' ? 'bg-rose-500 text-white animate-pulse' :
                      'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                    }`}>
                      {block.status}
                    </span>
                  </td>
                  <td className="py-2 px-3 text-slate-500 text-[11px] font-mono">
                    <span title={block.prev_hash}>{block.prev_hash.substring(0, 10)}...</span>
                  </td>
                  <td className="py-2 px-3 text-cyan-300 text-[11px] font-mono">
                    <span title={block.block_hash}>{block.block_hash.substring(0, 12)}...</span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
