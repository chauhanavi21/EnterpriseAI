'use client';

import { useEffect, useState } from 'react';
import Header from '@/components/Header';
import {
  Badge,
  Card,
  CardContent,
  EmptyState,
  LoadingSpinner,
  Pagination,
} from '@/components/ui';
import { tracesApi, Trace, TraceDetail } from '@/lib/api';
import { Activity, Clock, Coins, Hash, ChevronRight, X, Layers } from 'lucide-react';

export default function TracesPage() {
  const [traces, setTraces] = useState<Trace[]>([]);
  const [totalPages, setTotalPages] = useState(1);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<TraceDetail | null>(null);
  const [filters, setFilters] = useState<Record<string, string>>({});

  useEffect(() => {
    loadTraces();
  }, [page, filters]);

  async function loadTraces() {
    setLoading(true);
    try {
      const res = await tracesApi.list(page, filters);
      setTraces(res.items);
      setTotalPages(res.total_pages);
    } catch (err) {
      console.error('Failed to load traces:', err);
    } finally {
      setLoading(false);
    }
  }

  async function handleSelect(id: string) {
    try {
      const detail = await tracesApi.get(id);
      setSelected(detail);
    } catch (err) {
      console.error('Failed to load trace detail:', err);
    }
  }

  const statusVariant = (status: string): 'success' | 'warning' | 'error' | 'info' => {
    switch (status) {
      case 'completed': return 'success';
      case 'running': return 'warning';
      case 'error': return 'error';
      default: return 'info';
    }
  };

  const spanTypeColor = (type: string) => {
    const map: Record<string, string> = {
      llm: 'bg-purple-100 text-purple-700',
      retrieval: 'bg-blue-100 text-blue-700',
      tool: 'bg-orange-100 text-orange-700',
      chain: 'bg-green-100 text-green-700',
      embedding: 'bg-yellow-100 text-yellow-700',
      reranking: 'bg-pink-100 text-pink-700',
    };
    return map[type] || 'bg-gray-100 text-gray-700';
  };

  return (
    <>
      <Header
        title="Traces"
        subtitle="Observe and debug LLM interactions"
        actions={
          <div className="flex items-center gap-2">
            <select
              value={filters.status || ''}
              onChange={(e) => setFilters({ ...filters, status: e.target.value })}
              className="text-sm border border-gray-300 rounded-lg px-3 py-1.5 focus:ring-2 focus:ring-primary-500 outline-none"
            >
              <option value="">All statuses</option>
              <option value="completed">Completed</option>
              <option value="running">Running</option>
              <option value="error">Error</option>
            </select>
          </div>
        }
      />

      <div className="flex flex-1 overflow-hidden">
        {/* Trace list */}
        <div className={`${selected ? 'w-1/2' : 'w-full'} overflow-y-auto`}>
          <div className="p-6">
            {loading ? (
              <LoadingSpinner />
            ) : traces.length === 0 ? (
              <EmptyState
                icon={<Activity className="w-12 h-12 text-gray-300" />}
                title="No traces yet"
                description="Traces will appear here when you start chatting or running evaluations"
              />
            ) : (
              <div className="space-y-2">
                {traces.map((t) => (
                  <Card
                    key={t.id}
                    className={`p-4 cursor-pointer transition-all ${
                      selected?.id === t.id ? 'ring-2 ring-primary-500' : ''
                    }`}
                    onClick={() => handleSelect(t.id)}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="flex items-center gap-2">
                          <p className="text-sm font-medium text-gray-900">{t.name}</p>
                          <Badge variant={statusVariant(t.status)}>{t.status}</Badge>
                        </div>
                        <div className="flex items-center gap-4 mt-1.5 text-xs text-gray-400">
                          <span className="flex items-center gap-1">
                            <Hash className="w-3 h-3" />
                            {t.total_tokens.toLocaleString()} tokens
                          </span>
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {t.latency_ms}ms
                          </span>
                          <span className="flex items-center gap-1">
                            <Coins className="w-3 h-3" />
                            ${t.total_cost.toFixed(4)}
                          </span>
                          <span>{new Date(t.created_at).toLocaleString()}</span>
                        </div>
                      </div>
                      <ChevronRight className="w-4 h-4 text-gray-300" />
                    </div>
                  </Card>
                ))}
                <Pagination page={page} totalPages={totalPages} onPageChange={setPage} />
              </div>
            )}
          </div>
        </div>

        {/* Trace detail panel */}
        {selected && (
          <div className="w-1/2 border-l border-gray-200 bg-white overflow-y-auto">
            <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
              <div>
                <h3 className="text-base font-semibold text-gray-900">{selected.name}</h3>
                <p className="text-xs font-mono text-gray-400 mt-0.5">{selected.id}</p>
              </div>
              <button
                onClick={() => setSelected(null)}
                className="p-1 text-gray-400 hover:text-gray-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 space-y-6">
              {/* Summary */}
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-gray-50 rounded-lg p-3">
                  <p className="text-xs text-gray-500">Status</p>
                  <Badge variant={statusVariant(selected.status)}>{selected.status}</Badge>
                </div>
                <div className="bg-gray-50 rounded-lg p-3">
                  <p className="text-xs text-gray-500">Tokens</p>
                  <p className="text-sm font-medium text-gray-900">{selected.total_tokens.toLocaleString()}</p>
                </div>
                <div className="bg-gray-50 rounded-lg p-3">
                  <p className="text-xs text-gray-500">Latency</p>
                  <p className="text-sm font-medium text-gray-900">{selected.latency_ms}ms</p>
                </div>
              </div>

              {/* Input/Output */}
              {selected.input_data && (
                <div>
                  <p className="text-xs font-medium text-gray-500 mb-2">Input</p>
                  <pre className="text-xs bg-gray-50 rounded-lg p-3 text-gray-700 whitespace-pre-wrap font-mono overflow-auto max-h-40">
                    {typeof selected.input_data === 'string'
                      ? selected.input_data
                      : JSON.stringify(selected.input_data, null, 2)}
                  </pre>
                </div>
              )}

              {selected.output_data && (
                <div>
                  <p className="text-xs font-medium text-gray-500 mb-2">Output</p>
                  <pre className="text-xs bg-gray-50 rounded-lg p-3 text-gray-700 whitespace-pre-wrap font-mono overflow-auto max-h-40">
                    {typeof selected.output_data === 'string'
                      ? selected.output_data
                      : JSON.stringify(selected.output_data, null, 2)}
                  </pre>
                </div>
              )}

              {/* Spans */}
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <Layers className="w-4 h-4 text-gray-400" />
                  <p className="text-sm font-medium text-gray-900">
                    Spans ({selected.spans?.length || 0})
                  </p>
                </div>
                {selected.spans && selected.spans.length > 0 ? (
                  <div className="space-y-2">
                    {selected.spans.map((span) => (
                      <div
                        key={span.id}
                        className="border border-gray-100 rounded-lg p-3"
                      >
                        <div className="flex items-center justify-between mb-1">
                          <div className="flex items-center gap-2">
                            <span
                              className={`text-xs px-2 py-0.5 rounded-full font-medium ${spanTypeColor(
                                span.span_type
                              )}`}
                            >
                              {span.span_type}
                            </span>
                            <span className="text-sm font-medium text-gray-900">
                              {span.name}
                            </span>
                          </div>
                          <Badge variant={statusVariant(span.status)}>{span.status}</Badge>
                        </div>
                        <div className="flex items-center gap-4 text-xs text-gray-400 mt-1">
                          {span.model_name && <span>{span.model_name}</span>}
                          <span>{span.token_count} tokens</span>
                          <span>{span.latency_ms}ms</span>
                          <span>${span.cost.toFixed(4)}</span>
                        </div>
                        {span.error_message && (
                          <p className="mt-2 text-xs text-red-500">{span.error_message}</p>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-gray-400">No spans recorded</p>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
