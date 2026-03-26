'use client';

import { useEffect, useState, useRef } from 'react';
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
import { knowledgeApi, Document, PaginatedResponse, SearchResponse } from '@/lib/api';
import {
  Upload,
  FileText,
  Globe,
  Search,
  Trash2,
  Clock,
  HardDrive,
  AlertCircle,
  CheckCircle,
  Loader2,
  BookOpen,
} from 'lucide-react';

export default function KnowledgePage() {
  const { addToast } = useToast();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [totalPages, setTotalPages] = useState(1);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [showUpload, setShowUpload] = useState(false);
  const [showWeb, setShowWeb] = useState(false);
  const [webUrl, setWebUrl] = useState('');
  const [webTitle, setWebTitle] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResponse | null>(null);
  const [searching, setSearching] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const workspaceId = '00000000-0000-0000-0000-000000000001';

  useEffect(() => {
    loadDocuments();
  }, [page]);

  async function loadDocuments() {
    setLoading(true);
    try {
      const res = await knowledgeApi.listDocuments(workspaceId, page);
      setDocuments(res.items);
      setTotalPages(res.total_pages);
    } catch (err) {
      console.error('Failed to load documents:', err);
    } finally {
      setLoading(false);
    }
  }

  async function handleUpload(files: FileList | null) {
    if (!files || files.length === 0) return;
    setUploading(true);
    try {
      for (const file of Array.from(files)) {
        const form = new FormData();
        form.append('file', file);
        form.append('workspace_id', workspaceId);
        await knowledgeApi.uploadDocument(form);
      }
      addToast(`${files.length} file(s) uploaded successfully`, 'success');
      setShowUpload(false);
      loadDocuments();
    } catch (err: any) {
      addToast(err.error || 'Upload failed', 'error');
    } finally {
      setUploading(false);
    }
  }

  async function handleWebIngest() {
    if (!webUrl) return;
    try {
      await knowledgeApi.ingestWebPage({
        workspace_id: workspaceId,
        url: webUrl,
        title: webTitle || undefined,
      });
      addToast('Web page ingested successfully', 'success');
      setShowWeb(false);
      setWebUrl('');
      setWebTitle('');
      loadDocuments();
    } catch (err: any) {
      addToast(err.error || 'Web ingestion failed', 'error');
    }
  }

  async function handleSearch() {
    if (!searchQuery.trim()) return;
    setSearching(true);
    try {
      const res = await knowledgeApi.search({
        query: searchQuery,
        workspace_id: workspaceId,
        top_k: 10,
      });
      setSearchResults(res);
    } catch (err: any) {
      addToast(err.error || 'Search failed', 'error');
    } finally {
      setSearching(false);
    }
  }

  async function handleDelete(id: string) {
    if (!confirm('Are you sure you want to delete this document?')) return;
    try {
      await knowledgeApi.deleteDocument(id);
      addToast('Document deleted', 'success');
      loadDocuments();
    } catch (err: any) {
      addToast(err.error || 'Delete failed', 'error');
    }
  }

  const statusBadge = (status: string) => {
    const map: Record<string, { variant: 'success' | 'warning' | 'error' | 'info'; icon: any }> = {
      completed: { variant: 'success', icon: CheckCircle },
      processing: { variant: 'warning', icon: Loader2 },
      failed: { variant: 'error', icon: AlertCircle },
      pending: { variant: 'info', icon: Clock },
    };
    const s = map[status] || map.pending;
    const Icon = s.icon;
    return (
      <Badge variant={s.variant}>
        <Icon className={`w-3 h-3 mr-1 ${status === 'processing' ? 'animate-spin' : ''}`} />
        {status}
      </Badge>
    );
  };

  function formatBytes(bytes?: number): string {
    if (!bytes) return '—';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1048576).toFixed(1)} MB`;
  }

  return (
    <>
      <Header
        title="Knowledge Base"
        subtitle="Manage documents and search your knowledge"
        actions={
          <div className="flex items-center gap-2">
            <Button variant="secondary" size="sm" onClick={() => setShowWeb(true)}>
              <Globe className="w-4 h-4" /> Web Import
            </Button>
            <Button size="sm" onClick={() => setShowUpload(true)}>
              <Upload className="w-4 h-4" /> Upload
            </Button>
          </div>
        }
      />

      <div className="p-6 space-y-6">
        {/* Search bar */}
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                placeholder="Search your knowledge base..."
                className="w-full pl-9 pr-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
              />
            </div>
            <Button onClick={handleSearch} loading={searching} size="sm">
              Search
            </Button>
          </div>

          {/* Search results */}
          {searchResults && (
            <div className="mt-4 space-y-3">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-gray-900">
                  {searchResults.total_found} results
                  <span className="text-gray-400 font-normal ml-2">
                    ({searchResults.latency_ms}ms)
                  </span>
                </p>
                <button
                  onClick={() => setSearchResults(null)}
                  className="text-xs text-gray-400 hover:text-gray-600"
                >
                  Clear
                </button>
              </div>
              {searchResults.results.map((r, i) => (
                <div key={i} className="border border-gray-100 rounded-lg p-3">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium text-gray-900">
                      {r.document_title}
                    </span>
                    <span className="text-xs text-gray-400">
                      Score: {(r.score * 100).toFixed(1)}%
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 line-clamp-3">{r.content}</p>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* Documents list */}
        {loading ? (
          <LoadingSpinner />
        ) : documents.length === 0 ? (
          <EmptyState
            icon={<BookOpen className="w-12 h-12 text-gray-300" />}
            title="No documents yet"
            description="Upload files or import web pages to build your knowledge base"
            action={
              <Button onClick={() => setShowUpload(true)}>
                <Upload className="w-4 h-4" /> Upload Documents
              </Button>
            }
          />
        ) : (
          <div className="space-y-3">
            {documents.map((doc) => (
              <Card key={doc.id} className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="p-2 bg-gray-100 rounded-lg flex-shrink-0">
                      {doc.source_url ? (
                        <Globe className="w-5 h-5 text-gray-500" />
                      ) : (
                        <FileText className="w-5 h-5 text-gray-500" />
                      )}
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {doc.title}
                      </p>
                      <div className="flex items-center gap-3 mt-1">
                        {doc.file_type && (
                          <span className="text-xs text-gray-400 uppercase">
                            {doc.file_type}
                          </span>
                        )}
                        <span className="text-xs text-gray-400">
                          {formatBytes(doc.file_size_bytes)}
                        </span>
                        <span className="text-xs text-gray-400">
                          {doc.chunk_count} chunks
                        </span>
                        <span className="text-xs text-gray-400">
                          {new Date(doc.created_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 flex-shrink-0">
                    {statusBadge(doc.status)}
                    <button
                      onClick={() => handleDelete(doc.id)}
                      className="p-1.5 text-gray-400 hover:text-red-500 rounded transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
                {doc.error_message && (
                  <p className="mt-2 text-xs text-red-500">{doc.error_message}</p>
                )}
              </Card>
            ))}
            <Pagination page={page} totalPages={totalPages} onPageChange={setPage} />
          </div>
        )}
      </div>

      {/* Upload Modal */}
      <Modal
        open={showUpload}
        onClose={() => setShowUpload(false)}
        title="Upload Documents"
        footer={
          <Button onClick={() => fileInputRef.current?.click()} loading={uploading}>
            Select Files
          </Button>
        }
      >
        <div className="text-center py-8">
          <div
            className="border-2 border-dashed border-gray-300 rounded-xl p-8 hover:border-primary-400 transition-colors cursor-pointer"
            onClick={() => fileInputRef.current?.click()}
            onDragOver={(e) => { e.preventDefault(); e.stopPropagation(); }}
            onDrop={(e) => { e.preventDefault(); handleUpload(e.dataTransfer.files); }}
          >
            <Upload className="w-10 h-10 text-gray-300 mx-auto mb-3" />
            <p className="text-sm text-gray-600">
              Drag and drop files here, or click to browse
            </p>
            <p className="text-xs text-gray-400 mt-1">
              Supported: PDF, DOCX, TXT, HTML, CSV, JSON, Markdown
            </p>
          </div>
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept=".pdf,.docx,.txt,.html,.csv,.json,.md"
            className="hidden"
            onChange={(e) => handleUpload(e.target.files)}
          />
        </div>
      </Modal>

      {/* Web Import Modal */}
      <Modal
        open={showWeb}
        onClose={() => setShowWeb(false)}
        title="Import Web Page"
        footer={<Button onClick={handleWebIngest}>Import</Button>}
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">URL</label>
            <input
              type="url"
              value={webUrl}
              onChange={(e) => setWebUrl(e.target.value)}
              placeholder="https://example.com/docs"
              className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Title (optional)
            </label>
            <input
              type="text"
              value={webTitle}
              onChange={(e) => setWebTitle(e.target.value)}
              placeholder="Auto-detected from page"
              className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
            />
          </div>
        </div>
      </Modal>
    </>
  );
}
