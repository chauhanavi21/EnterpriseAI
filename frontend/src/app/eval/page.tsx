'use client';

import { useEffect, useState } from 'react';
import Header from '@/components/Header';
import {
  Button,
  Badge,
  Card,
  CardContent,
  CardHeader,
  EmptyState,
  LoadingSpinner,
  Modal,
  Pagination,
  StatCard,
  useToast,
} from '@/components/ui';
import { evalApi, EvalDataset, Experiment, ExperimentDetail } from '@/lib/api';
import {
  Sparkles,
  Plus,
  Play,
  BarChart3,
  Database,
  Clock,
  CheckCircle,
  AlertCircle,
  Loader2,
} from 'lucide-react';

export default function EvalPage() {
  const { addToast } = useToast();
  const [tab, setTab] = useState<'datasets' | 'experiments'>('experiments');
  const [datasets, setDatasets] = useState<EvalDataset[]>([]);
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [dsPage, setDsPage] = useState(1);
  const [dsTotalPages, setDsTotalPages] = useState(1);
  const [expPage, setExpPage] = useState(1);
  const [expTotalPages, setExpTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [selectedExp, setSelectedExp] = useState<ExperimentDetail | null>(null);

  // Modals
  const [showCreateDataset, setShowCreateDataset] = useState(false);
  const [dsName, setDsName] = useState('');
  const [dsDesc, setDsDesc] = useState('');
  const [showRunExp, setShowRunExp] = useState(false);
  const [expName, setExpName] = useState('');
  const [expDatasetId, setExpDatasetId] = useState('');

  useEffect(() => {
    loadData();
  }, [tab, dsPage, expPage]);

  async function loadData() {
    setLoading(true);
    try {
      if (tab === 'datasets') {
        const res = await evalApi.listDatasets(dsPage);
        setDatasets(res.items);
        setDsTotalPages(res.total_pages);
      } else {
        const res = await evalApi.listExperiments(expPage);
        setExperiments(res.items);
        setExpTotalPages(res.total_pages);
      }
    } catch (err) {
      console.error('Failed to load:', err);
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateDataset() {
    if (!dsName.trim()) return;
    try {
      await evalApi.createDataset({ name: dsName, description: dsDesc || undefined });
      addToast('Dataset created', 'success');
      setShowCreateDataset(false);
      setDsName('');
      setDsDesc('');
      loadData();
    } catch (err: any) {
      addToast(err.error || 'Failed to create dataset', 'error');
    }
  }

  async function handleRunExperiment() {
    if (!expName.trim() || !expDatasetId) return;
    try {
      const exp = await evalApi.createExperiment({
        name: expName,
        dataset_id: expDatasetId,
      });
      await evalApi.runExperiment(exp.id);
      addToast('Experiment started', 'success');
      setShowRunExp(false);
      setExpName('');
      setExpDatasetId('');
      setTab('experiments');
      loadData();
    } catch (err: any) {
      addToast(err.error || 'Failed to run experiment', 'error');
    }
  }

  async function handleSelectExperiment(id: string) {
    try {
      const detail = await evalApi.getExperiment(id);
      setSelectedExp(detail);
    } catch (err: any) {
      addToast(err.error || 'Failed to load experiment', 'error');
    }
  }

  const expStatusVariant = (status: string): 'success' | 'warning' | 'error' | 'info' => {
    switch (status) {
      case 'completed': return 'success';
      case 'running': return 'warning';
      case 'failed': return 'error';
      default: return 'info';
    }
  };

  const metricColor = (score: number): string => {
    if (score >= 0.8) return 'text-green-600';
    if (score >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <>
      <Header
        title="Evaluation"
        subtitle="Measure RAG pipeline quality with Ragas-inspired metrics"
        actions={
          <div className="flex items-center gap-2">
            <Button variant="secondary" size="sm" onClick={() => setShowCreateDataset(true)}>
              <Database className="w-4 h-4" /> New Dataset
            </Button>
            <Button size="sm" onClick={() => { setShowRunExp(true); loadDatasets(); }}>
              <Play className="w-4 h-4" /> Run Experiment
            </Button>
          </div>
        }
      />

      {/* Tabs */}
      <div className="border-b border-gray-200 px-6">
        <nav className="flex gap-6 -mb-px">
          {['experiments', 'datasets'].map((t) => (
            <button
              key={t}
              onClick={() => setTab(t as any)}
              className={`py-3 text-sm font-medium border-b-2 transition-colors ${
                tab === t
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              {t.charAt(0).toUpperCase() + t.slice(1)}
            </button>
          ))}
        </nav>
      </div>

      <div className="flex flex-1 overflow-hidden">
        <div className={`${selectedExp ? 'w-1/2' : 'w-full'} p-6 overflow-y-auto`}>
          {loading ? (
            <LoadingSpinner />
          ) : tab === 'experiments' ? (
            experiments.length === 0 ? (
              <EmptyState
                icon={<Sparkles className="w-12 h-12 text-gray-300" />}
                title="No experiments yet"
                description="Run your first evaluation experiment to measure RAG quality"
                action={
                  <Button onClick={() => setShowRunExp(true)}>
                    <Play className="w-4 h-4" /> Run Experiment
                  </Button>
                }
              />
            ) : (
              <div className="space-y-3">
                {experiments.map((exp) => (
                  <Card
                    key={exp.id}
                    className={`p-4 cursor-pointer ${
                      selectedExp?.id === exp.id ? 'ring-2 ring-primary-500' : ''
                    }`}
                    onClick={() => handleSelectExperiment(exp.id)}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="flex items-center gap-2">
                          <p className="text-sm font-medium text-gray-900">{exp.name}</p>
                          <Badge variant={expStatusVariant(exp.status)}>{exp.status}</Badge>
                        </div>
                        <p className="text-xs text-gray-400 mt-1">
                          Created {new Date(exp.created_at).toLocaleString()}
                        </p>
                      </div>
                      {exp.results_summary && (
                        <div className="flex items-center gap-3">
                          {Object.entries(exp.results_summary).slice(0, 3).map(([k, v]) => (
                            <div key={k} className="text-center">
                              <p className={`text-lg font-semibold ${metricColor(v)}`}>
                                {(v * 100).toFixed(0)}%
                              </p>
                              <p className="text-xs text-gray-400 capitalize">
                                {k.replace(/_/g, ' ')}
                              </p>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </Card>
                ))}
                <Pagination page={expPage} totalPages={expTotalPages} onPageChange={setExpPage} />
              </div>
            )
          ) : (
            /* Datasets tab */
            datasets.length === 0 ? (
              <EmptyState
                icon={<Database className="w-12 h-12 text-gray-300" />}
                title="No datasets yet"
                description="Create a dataset with question-answer pairs for evaluation"
                action={
                  <Button onClick={() => setShowCreateDataset(true)}>
                    <Plus className="w-4 h-4" /> Create Dataset
                  </Button>
                }
              />
            ) : (
              <div className="space-y-3">
                {datasets.map((ds) => (
                  <Card key={ds.id} className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-900">{ds.name}</p>
                        <p className="text-xs text-gray-400 mt-1">{ds.description || 'No description'}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-medium text-gray-900">{ds.item_count} items</p>
                        <p className="text-xs text-gray-400">{new Date(ds.created_at).toLocaleDateString()}</p>
                      </div>
                    </div>
                  </Card>
                ))}
                <Pagination page={dsPage} totalPages={dsTotalPages} onPageChange={setDsPage} />
              </div>
            )
          )}
        </div>

        {/* Experiment detail */}
        {selectedExp && (
          <div className="w-1/2 border-l border-gray-200 bg-white overflow-y-auto p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-base font-semibold text-gray-900">{selectedExp.name}</h3>
                <Badge variant={expStatusVariant(selectedExp.status)}>{selectedExp.status}</Badge>
              </div>
              <button
                onClick={() => setSelectedExp(null)}
                className="text-gray-400 hover:text-gray-600 text-sm"
              >
                Close
              </button>
            </div>

            {/* Scores */}
            {selectedExp.scores && selectedExp.scores.length > 0 ? (
              <div className="space-y-4">
                <h4 className="text-sm font-medium text-gray-900">Evaluation Scores</h4>
                <div className="grid grid-cols-2 gap-3">
                  {selectedExp.scores.map((score) => (
                    <div key={score.id} className="bg-gray-50 rounded-lg p-4">
                      <p className="text-xs text-gray-500 capitalize">
                        {score.metric.replace(/_/g, ' ')}
                      </p>
                      <p className={`text-2xl font-bold mt-1 ${metricColor(score.score)}`}>
                        {(score.score * 100).toFixed(1)}%
                      </p>
                      {score.reasoning && (
                        <p className="text-xs text-gray-400 mt-1 line-clamp-2">{score.reasoning}</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <p className="text-sm text-gray-400">
                {selectedExp.status === 'running'
                  ? 'Experiment is running... scores will appear shortly.'
                  : 'No scores available.'}
              </p>
            )}

            {selectedExp.results_summary && (
              <div className="mt-6">
                <h4 className="text-sm font-medium text-gray-900 mb-3">Summary</h4>
                <pre className="text-xs bg-gray-50 rounded-lg p-3 font-mono text-gray-700">
                  {JSON.stringify(selectedExp.results_summary, null, 2)}
                </pre>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Create Dataset Modal */}
      <Modal
        open={showCreateDataset}
        onClose={() => setShowCreateDataset(false)}
        title="New Evaluation Dataset"
        footer={<Button onClick={handleCreateDataset}>Create</Button>}
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
            <input
              value={dsName}
              onChange={(e) => setDsName(e.target.value)}
              placeholder="e.g. rag-qa-benchmark"
              className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 outline-none"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea
              value={dsDesc}
              onChange={(e) => setDsDesc(e.target.value)}
              rows={2}
              placeholder="Describe the evaluation dataset..."
              className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 outline-none"
            />
          </div>
        </div>
      </Modal>

      {/* Run Experiment Modal */}
      <Modal
        open={showRunExp}
        onClose={() => setShowRunExp(false)}
        title="Run Evaluation Experiment"
        footer={<Button onClick={handleRunExperiment}>Start Experiment</Button>}
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
            <input
              value={expName}
              onChange={(e) => setExpName(e.target.value)}
              placeholder="e.g. baseline-v1"
              className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 outline-none"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Dataset</label>
            <select
              value={expDatasetId}
              onChange={(e) => setExpDatasetId(e.target.value)}
              className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 outline-none"
            >
              <option value="">Select a dataset</option>
              {datasets.map((ds) => (
                <option key={ds.id} value={ds.id}>
                  {ds.name} ({ds.item_count} items)
                </option>
              ))}
            </select>
          </div>
        </div>
      </Modal>
    </>
  );

  // Helper to load datasets for dropdown
  async function loadDatasets() {
    try {
      const res = await evalApi.listDatasets(1);
      setDatasets(res.items);
    } catch (err) {
      console.error(err);
    }
  }
}
