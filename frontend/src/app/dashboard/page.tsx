'use client';

import { useEffect, useState } from 'react';
import Header from '@/components/Header';
import { StatCard, Card, CardContent, LoadingSpinner, Badge } from '@/components/ui';
import { chatApi, knowledgeApi, evalApi, feedbackApi, tracesApi } from '@/lib/api';
import {
  MessageSquare,
  FileText,
  Activity,
  ThumbsUp,
  TrendingUp,
  Clock,
} from 'lucide-react';

interface DashboardStats {
  conversations: number;
  documents: number;
  traces: number;
  feedbackPositive: number;
  feedbackTotal: number;
  experiments: number;
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [recentTraces, setRecentTraces] = useState<any[]>([]);

  useEffect(() => {
    loadDashboard();
  }, []);

  async function loadDashboard() {
    try {
      // Load in parallel
      const [feedbackStats, traceResp, experimentResp] = await Promise.allSettled([
        feedbackApi.stats(),
        tracesApi.list(1),
        evalApi.listExperiments(1),
      ]);

      const fb = feedbackStats.status === 'fulfilled' ? feedbackStats.value : null;
      const tr = traceResp.status === 'fulfilled' ? traceResp.value : null;
      const ex = experimentResp.status === 'fulfilled' ? experimentResp.value : null;

      setStats({
        conversations: 0,
        documents: 0,
        traces: tr?.total || 0,
        feedbackPositive: fb?.thumbs_up || 0,
        feedbackTotal: fb?.total || 0,
        experiments: ex?.total || 0,
      });

      if (tr?.items) {
        setRecentTraces(tr.items.slice(0, 5));
      }
    } catch (err) {
      console.error('Failed to load dashboard:', err);
    } finally {
      setLoading(false);
    }
  }

  if (loading) return <LoadingSpinner />;

  const satisfactionRate =
    stats && stats.feedbackTotal > 0
      ? Math.round((stats.feedbackPositive / stats.feedbackTotal) * 100)
      : 0;

  return (
    <>
      <Header title="Dashboard" subtitle="Overview of your AI knowledge platform" />

      <div className="p-6 space-y-6">
        {/* Stat cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            label="Total Traces"
            value={stats?.traces || 0}
            subtext="LLM interactions tracked"
            icon={<Activity className="w-5 h-5" />}
          />
          <StatCard
            label="Experiments"
            value={stats?.experiments || 0}
            subtext="Evaluation runs"
            icon={<TrendingUp className="w-5 h-5" />}
          />
          <StatCard
            label="Feedback"
            value={stats?.feedbackTotal || 0}
            subtext={`${satisfactionRate}% satisfaction`}
            icon={<ThumbsUp className="w-5 h-5" />}
          />
          <StatCard
            label="Satisfaction"
            value={`${satisfactionRate}%`}
            subtext={`${stats?.feedbackPositive || 0} positive ratings`}
            icon={<MessageSquare className="w-5 h-5" />}
          />
        </div>

        {/* Recent traces */}
        <Card>
          <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
            <h2 className="text-base font-semibold text-gray-900">Recent Traces</h2>
            <a href="/traces" className="text-sm text-primary-600 hover:text-primary-700">
              View all
            </a>
          </div>
          <CardContent className="p-0">
            {recentTraces.length > 0 ? (
              <table className="w-full">
                <thead>
                  <tr className="text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    <th className="px-6 py-3">Name</th>
                    <th className="px-6 py-3">Status</th>
                    <th className="px-6 py-3">Tokens</th>
                    <th className="px-6 py-3">Latency</th>
                    <th className="px-6 py-3">Time</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {recentTraces.map((trace) => (
                    <tr key={trace.id} className="hover:bg-gray-50">
                      <td className="px-6 py-3 text-sm font-medium text-gray-900">
                        {trace.name}
                      </td>
                      <td className="px-6 py-3">
                        <Badge
                          variant={
                            trace.status === 'completed'
                              ? 'success'
                              : trace.status === 'error'
                              ? 'error'
                              : 'warning'
                          }
                        >
                          {trace.status}
                        </Badge>
                      </td>
                      <td className="px-6 py-3 text-sm text-gray-600">
                        {trace.total_tokens?.toLocaleString() || '—'}
                      </td>
                      <td className="px-6 py-3 text-sm text-gray-600">
                        {trace.latency_ms ? `${trace.latency_ms}ms` : '—'}
                      </td>
                      <td className="px-6 py-3 text-sm text-gray-400">
                        {new Date(trace.created_at).toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="text-center py-12 text-gray-400 text-sm">
                No traces recorded yet. Start chatting to generate traces.
              </div>
            )}
          </CardContent>
        </Card>

        {/* Quick actions */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card className="p-5 hover:border-primary-300 transition-colors cursor-pointer" onClick={() => (window.location.href = '/chat')}>
            <div className="flex items-center gap-3">
              <div className="p-2 bg-primary-100 rounded-lg">
                <MessageSquare className="w-5 h-5 text-primary-600" />
              </div>
              <div>
                <p className="font-medium text-gray-900 text-sm">Start a Chat</p>
                <p className="text-xs text-gray-500">Ask questions against your knowledge base</p>
              </div>
            </div>
          </Card>
          <Card className="p-5 hover:border-primary-300 transition-colors cursor-pointer" onClick={() => (window.location.href = '/knowledge')}>
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <FileText className="w-5 h-5 text-green-600" />
              </div>
              <div>
                <p className="font-medium text-gray-900 text-sm">Upload Documents</p>
                <p className="text-xs text-gray-500">Add files to your knowledge base</p>
              </div>
            </div>
          </Card>
          <Card className="p-5 hover:border-primary-300 transition-colors cursor-pointer" onClick={() => (window.location.href = '/eval')}>
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 rounded-lg">
                <TrendingUp className="w-5 h-5 text-purple-600" />
              </div>
              <div>
                <p className="font-medium text-gray-900 text-sm">Run Evaluation</p>
                <p className="text-xs text-gray-500">Measure your RAG pipeline quality</p>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </>
  );
}
