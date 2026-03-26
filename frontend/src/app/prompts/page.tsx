'use client';

import { useEffect, useState } from 'react';
import Header from '@/components/Header';
import {
  Button,
  Badge,
  Card,
  CardContent,
  EmptyState,
  LoadingSpinner,
  Modal,
  Pagination,
  useToast,
} from '@/components/ui';
import { promptsApi, PromptTemplate, PromptTemplateDetail, PromptVersion } from '@/lib/api';
import { FileText, Plus, Tag, Clock, ArrowUp, Copy, Code } from 'lucide-react';

export default function PromptsPage() {
  const { addToast } = useToast();
  const [templates, setTemplates] = useState<PromptTemplate[]>([]);
  const [totalPages, setTotalPages] = useState(1);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [selected, setSelected] = useState<PromptTemplateDetail | null>(null);
  const [showVersion, setShowVersion] = useState(false);
  const [versionContent, setVersionContent] = useState('');
  const [versionSystem, setVersionSystem] = useState('');

  useEffect(() => {
    loadTemplates();
  }, [page]);

  async function loadTemplates() {
    setLoading(true);
    try {
      const res = await promptsApi.listTemplates(page);
      setTemplates(res.items);
      setTotalPages(res.total_pages);
    } catch (err) {
      console.error('Failed to load templates:', err);
    } finally {
      setLoading(false);
    }
  }

  async function handleCreate() {
    if (!newName.trim()) return;
    try {
      await promptsApi.createTemplate({ name: newName, description: newDesc || undefined });
      addToast('Template created', 'success');
      setShowCreate(false);
      setNewName('');
      setNewDesc('');
      loadTemplates();
    } catch (err: any) {
      addToast(err.error || 'Failed to create template', 'error');
    }
  }

  async function handleSelect(id: string) {
    try {
      const detail = await promptsApi.getTemplate(id);
      setSelected(detail);
    } catch (err: any) {
      addToast(err.error || 'Failed to load template', 'error');
    }
  }

  async function handleCreateVersion() {
    if (!selected || !versionContent.trim()) return;
    try {
      await promptsApi.createVersion(selected.id, {
        content: versionContent,
        system_prompt: versionSystem || undefined,
      });
      addToast('Version created', 'success');
      setShowVersion(false);
      setVersionContent('');
      setVersionSystem('');
      handleSelect(selected.id);
    } catch (err: any) {
      addToast(err.error || 'Failed to create version', 'error');
    }
  }

  async function handlePromote(versionId: string, label: string) {
    try {
      await promptsApi.updateLabel(versionId, label);
      addToast(`Version promoted to ${label}`, 'success');
      if (selected) handleSelect(selected.id);
    } catch (err: any) {
      addToast(err.error || 'Failed to update label', 'error');
    }
  }

  const labelBadge = (label: string) => {
    const map: Record<string, 'success' | 'warning' | 'info' | 'default'> = {
      production: 'success',
      staging: 'warning',
      draft: 'info',
      archived: 'default',
    };
    return <Badge variant={map[label] || 'default'}>{label}</Badge>;
  };

  return (
    <>
      <Header
        title="Prompt Registry"
        subtitle="Manage and version your prompt templates"
        actions={
          <Button size="sm" onClick={() => setShowCreate(true)}>
            <Plus className="w-4 h-4" /> New Template
          </Button>
        }
      />

      <div className="flex flex-1 overflow-hidden">
        {/* Template list */}
        <div className="w-80 border-r border-gray-200 bg-white overflow-y-auto">
          {loading ? (
            <LoadingSpinner size="sm" />
          ) : templates.length === 0 ? (
            <div className="p-6 text-center text-sm text-gray-400">
              No prompt templates yet
            </div>
          ) : (
            <>
              {templates.map((t) => (
                <button
                  key={t.id}
                  onClick={() => handleSelect(t.id)}
                  className={`w-full text-left px-4 py-3 border-b border-gray-100 hover:bg-gray-50 transition-colors ${
                    selected?.id === t.id ? 'bg-primary-50 border-l-2 border-l-primary-500' : ''
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <Code className="w-4 h-4 text-gray-400 flex-shrink-0" />
                    <p className="text-sm font-medium text-gray-900 truncate">{t.name}</p>
                  </div>
                  <p className="text-xs text-gray-400 mt-1 truncate">{t.description || 'No description'}</p>
                </button>
              ))}
              <div className="p-3">
                <Pagination page={page} totalPages={totalPages} onPageChange={setPage} />
              </div>
            </>
          )}
        </div>

        {/* Version detail */}
        <div className="flex-1 overflow-y-auto p-6">
          {!selected ? (
            <EmptyState
              icon={<FileText className="w-12 h-12 text-gray-300" />}
              title="Select a template"
              description="Choose a prompt template from the list to view its versions"
            />
          ) : (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-semibold text-gray-900">{selected.name}</h2>
                  <p className="text-sm text-gray-500">{selected.description}</p>
                </div>
                <Button size="sm" onClick={() => setShowVersion(true)}>
                  <Plus className="w-4 h-4" /> New Version
                </Button>
              </div>

              {/* Versions */}
              {selected.versions && selected.versions.length > 0 ? (
                <div className="space-y-4">
                  {selected.versions.map((v) => (
                    <Card key={v.id}>
                      <div className="px-5 py-3 border-b border-gray-100 flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <span className="text-sm font-mono font-medium text-gray-900">
                            v{v.version_number}
                          </span>
                          {labelBadge(v.label)}
                        </div>
                        <div className="flex items-center gap-2">
                          {v.label !== 'production' && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handlePromote(v.id, 'production')}
                            >
                              <ArrowUp className="w-3 h-3" /> Promote
                            </Button>
                          )}
                          <span className="text-xs text-gray-400">
                            {new Date(v.created_at).toLocaleDateString()}
                          </span>
                        </div>
                      </div>
                      <CardContent>
                        {v.system_prompt && (
                          <div className="mb-3">
                            <p className="text-xs font-medium text-gray-500 mb-1">System Prompt</p>
                            <pre className="text-xs bg-gray-50 rounded-lg p-3 text-gray-700 whitespace-pre-wrap font-mono">
                              {v.system_prompt}
                            </pre>
                          </div>
                        )}
                        <div>
                          <p className="text-xs font-medium text-gray-500 mb-1">Content</p>
                          <pre className="text-xs bg-gray-50 rounded-lg p-3 text-gray-700 whitespace-pre-wrap font-mono">
                            {v.content}
                          </pre>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              ) : (
                <EmptyState
                  title="No versions"
                  description="Create the first version for this template"
                />
              )}
            </div>
          )}
        </div>
      </div>

      {/* Create Template Modal */}
      <Modal
        open={showCreate}
        onClose={() => setShowCreate(false)}
        title="New Prompt Template"
        footer={<Button onClick={handleCreate}>Create</Button>}
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
            <input
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="e.g. rag-qa-v2"
              className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea
              value={newDesc}
              onChange={(e) => setNewDesc(e.target.value)}
              rows={2}
              placeholder="What this prompt template is used for..."
              className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
            />
          </div>
        </div>
      </Modal>

      {/* Create Version Modal */}
      <Modal
        open={showVersion}
        onClose={() => setShowVersion(false)}
        title="New Version"
        footer={<Button onClick={handleCreateVersion}>Create Version</Button>}
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">System Prompt</label>
            <textarea
              value={versionSystem}
              onChange={(e) => setVersionSystem(e.target.value)}
              rows={3}
              placeholder="You are a helpful assistant..."
              className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm font-mono focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Content</label>
            <textarea
              value={versionContent}
              onChange={(e) => setVersionContent(e.target.value)}
              rows={6}
              placeholder="Use {{context}} and {{question}} placeholders..."
              className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm font-mono focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
            />
          </div>
        </div>
      </Modal>
    </>
  );
}
