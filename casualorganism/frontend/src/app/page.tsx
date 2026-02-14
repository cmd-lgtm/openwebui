'use client';

import { useEffect, useState } from 'react';
import { api, GraphStats, CausalResults } from '@/lib/api';
import { useWebSocket } from '@/lib/useWebSocket';
import { Network, Activity, BrainCircuit, Users, Wifi, WifiOff } from 'lucide-react';
import { motion } from 'framer-motion';

export default function Home() {
  const [stats, setStats] = useState<GraphStats | null>(null);
  const [analysis, setAnalysis] = useState<CausalResults | null>(null);
  const [loading, setLoading] = useState(true);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected' | 'failed'>('disconnected');

  // WebSocket for real-time updates
  const { connectionState, lastMessage, reconnect } = useWebSocket({
    channel: 'graph',
    onMessage: (message) => {
      // Handle real-time updates
      if (message.type === 'graph_update' && message.data) {
        // Update stats if received via WebSocket
        if (message.data.node_count !== undefined) {
          setStats(prev => prev ? { ...prev, ...message.data } : message.data);
        }
      }
    },
    onConnect: () => setConnectionStatus('connected'),
    onDisconnect: () => setConnectionStatus('disconnected'),
    onError: () => setConnectionStatus('failed'),
    // Enable polling fallback after 5 seconds if WebSocket fails
    fallbackPolling: true,
    pollingFetcher: async () => {
      try {
        return await api.getStats();
      } catch {
        return null;
      }
    },
  });

  useEffect(() => {
    async function loadData() {
      try {
        // 1. Get Live Stats (initial load)
        const s = await api.getStats();
        setStats(s);

        // 2. Trigger Causal Analysis (Async)
        const { task_id } = await api.triggerAnalysis();
        console.log(`Analysis started. Task ID: ${task_id}`);

        // 3. Poll for Results (using longer interval now)
        const poll = setInterval(async () => {
            const task = await api.pollTask(task_id);
            console.log(`Task Status: ${task.status}`);

            if (task.status === 'SUCCESS' && task.result) {
                setAnalysis(task.result);
                setLoading(false);
                clearInterval(poll);
            } else if (task.status === 'FAILURE') {
                console.error("Analysis failed");
                setLoading(false);
                clearInterval(poll);
            }
        }, 5000); // Poll every 5s (less aggressive since we have WebSocket)

      } catch (e) {
        console.error(e);
        setLoading(false);
      }
    }
    loadData();
  }, []);

  // Update stats when WebSocket message arrives
  useEffect(() => {
    if (lastMessage?.type === 'graph_update' && lastMessage.data) {
      if (lastMessage.data.node_count !== undefined) {
        setStats(lastMessage.data);
      }
    }
  }, [lastMessage]);

  if (loading) return <div className="min-h-screen bg-neutral-900 text-white flex items-center justify-center">Initializing Causal System...</div>;

  return (
    <main className="min-h-screen bg-black text-white p-8 font-sans selection:bg-purple-500/30">
      <header className="mb-12 border-b border-neutral-800 pb-6 flex justify-between items-center">
        <div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-400 to-blue-500 bg-clip-text text-transparent">
            Causal Organism
          </h1>
          <p className="text-neutral-400 mt-2">Autonomous Enterprise Optimization Platform</p>
        </div>
        <div className="flex gap-4">
             <ConnectionIndicator
               status={connectionState}
               onReconnect={reconnect}
             />
             <div className="px-4 py-2 bg-green-500/10 text-green-400 rounded-full border border-green-500/20 text-sm font-mono flex items-center gap-2">
                <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                SYSTEM ACTIVE
             </div>
        </div>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
        <StatCard
          title="Active Nodes"
          value={stats?.node_count || 0}
          icon={<Users className="w-6 h-6 text-blue-400"/>}
          desc="Employees Monitored"
        />
        <StatCard
          title="Interaction Volume"
          value={stats?.edge_count || 0}
          icon={<Activity className="w-6 h-6 text-purple-400"/>}
          desc="Signal Events / Hour"
        />
        <StatCard
          title="Network Density"
          value={stats?.density.toFixed(3) || 0}
          icon={<Network className="w-6 h-6 text-pink-400"/>}
          desc="Connectedness Score"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Causal Discovery Section */}
        <section className="bg-neutral-900/50 border border-neutral-800 rounded-2xl p-8 backdrop-blur-sm">
          <div className="flex items-center gap-3 mb-6">
            <BrainCircuit className="w-8 h-8 text-yellow-500" />
            <h2 className="text-2xl font-semibold">Causal Discovery Engine</h2>
          </div>

          <div className="space-y-6">
             <div className="p-4 bg-black/40 rounded-xl border border-neutral-800">
                <h3 className="text-lg font-medium text-neutral-300 mb-2">Hypothesis: Burnout Drivers</h3>
                <p className="text-neutral-400 text-sm mb-4">Regression Analysis: Burnout ~ Centrality + Role</p>

                <div className="grid grid-cols-2 gap-4">
                    <MetricBox label="Intercept (Base Stress)" value={analysis?.coefficients.intercept.toFixed(1)} />
                    <MetricBox label="R-Squared (Confidence)" value={analysis?.r_squared.toFixed(2)} highlight />
                </div>
             </div>

             <div className="space-y-3">
                <CausalInsight
                    label="Effect of High Communication (Centrality)"
                    value={analysis?.coefficients.degree_centrality.toFixed(1)}
                    impact="negative" // Increases burnout
                    desc="For every 1% increase in centrality, burnout increases significantly."
                />
                <CausalInsight
                    label="Effect of Manager Role"
                    value={analysis?.coefficients.is_manager.toFixed(1)}
                    impact="positive" // Decreases burnout
                    desc="Managers effectively buffer this stress (Resilience Factor)."
                />
             </div>
          </div>
        </section>

        {/* Action/Simulation Section Placeholder */}
        <section className="bg-neutral-900/50 border border-neutral-800 rounded-2xl p-8 backdrop-blur-sm flex flex-col justify-center items-center text-center">
            <div className="w-16 h-16 bg-blue-500/20 rounded-full flex items-center justify-center mb-4">
                 <Activity className="w-8 h-8 text-blue-400" />
            </div>
            <h3 className="text-xl font-semibold mb-2">Autonomous Interventions</h3>
            <p className="text-neutral-400 max-w-md">
                The Action Orchestrator is running in background.
                It automatically schedules "Deep Work" for employees with high Burnout Probability (&gt;80%).
            </p>
            <button className="mt-6 px-6 py-3 bg-white text-black font-semibold rounded-lg hover:bg-neutral-200 transition-colors">
                View Intervention Log
            </button>
        </section>
      </div>
    </main>
  );
}

/**
 * Connection status indicator component.
 * Shows real-time connection state with WebSocket/polling status.
 */
function ConnectionIndicator({ status, onReconnect }: { status: string; onReconnect: () => void }) {
  const statusConfig = {
    connecting: { color: 'yellow', icon: Wifi, text: 'Connecting...' },
    connected: { color: 'green', icon: Wifi, text: 'Live' },
    disconnected: { color: 'neutral', icon: WifiOff, text: 'Disconnected' },
    failed: { color: 'red', icon: WifiOff, text: 'Using Polling' },
  };

  const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.disconnected;
  const Icon = config.icon;

  return (
    <button
      onClick={onReconnect}
      className={`px-4 py-2 bg-${config.color}-500/10 text-${config.color}-400 rounded-full border border-${config.color}-500/20 text-sm font-mono flex items-center gap-2 hover:bg-${config.color}-500/20 transition-colors`}
      title={status === 'failed' ? 'WebSocket unavailable, using HTTP polling' : 'Click to reconnect'}
    >
      <Icon className="w-4 h-4" />
      {config.text}
    </button>
  );
}

function StatCard({ title, value, icon, desc }: any) {
    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="p-6 bg-neutral-900 rounded-xl border border-neutral-800 hover:border-neutral-700 transition-colors"
        >
            <div className="flex justify-between items-start mb-4">
                <div className="p-3 bg-neutral-800 rounded-lg">{icon}</div>
                <span className="text-3xl font-bold">{value}</span>
            </div>
            <h3 className="text-lg font-medium text-neutral-200">{title}</h3>
            <p className="text-sm text-neutral-500">{desc}</p>
        </motion.div>
    )
}

function MetricBox({ label, value, highlight }: any) {
    return (
        <div className={`p-3 rounded-lg ${highlight ? 'bg-blue-500/10 border-blue-500/30' : 'bg-neutral-800'}`}>
            <div className="text-xs text-neutral-400 uppercase tracking-wider">{label}</div>
            <div className={`text-xl font-bold ${highlight ? 'text-blue-400' : 'text-white'}`}>{value}</div>
        </div>
    )
}

function CausalInsight({ label, value, impact, desc }: any) {
    const color = impact === 'negative' ? 'text-red-400' : 'text-green-400';
    return (
        <div className="flex items-center justify-between p-4 bg-neutral-800/50 rounded-lg border border-neutral-800">
            <div>
                <div className="font-medium text-neutral-200">{label}</div>
                <div className="text-xs text-neutral-500 mt-1">{desc}</div>
            </div>
            <div className={`text-2xl font-bold font-mono ${color}`}>
                {Number(value) > 0 ? '+' : ''}{value}
            </div>
        </div>
    )
}
