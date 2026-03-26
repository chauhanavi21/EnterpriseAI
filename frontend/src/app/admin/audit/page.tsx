'use client';

import { useEffect, useState } from 'react';
import Header from '@/components/Header';
import {
  Badge,
  Card,
  EmptyState,
  LoadingSpinner,
  Pagination,
} from '@/components/ui';
import { adminApi, AuditLog, PaginatedResponse } from '@/lib/api';
import { Shield, Clock, User, FileText } from 'lucide-react';

export default function AuditPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadLogs();
  }, [page]);

  async function loadLogs() {
    setLoading(true);
    try {
      const res = await adminApi.listAuditLogs(page);
      setLogs(res.items);
      setTotalPages(res.total_pages);
    } catch (err) {
      console.error('Failed to load audit logs:', err);
    } finally {
      setLoading(false);
    }
  }

  const actionColor = (action: string) => {
    if (action.includes('create') || action.includes('register')) return 'success';
    if (action.includes('delete') || action.includes('revoke')) return 'error';
    if (action.includes('update') || action.includes('promote')) return 'warning';
    return 'info';
  };

  return (
    <>
      <Header title="Audit Logs" subtitle="Track all system actions and changes" />

      <div className="p-6">
        {loading ? (
          <LoadingSpinner />
        ) : logs.length === 0 ? (
          <EmptyState
            icon={<Shield className="w-12 h-12 text-gray-300" />}
            title="No audit logs"
            description="System actions will be recorded here"
          />
        ) : (
          <div className="space-y-2">
            {logs.map((log) => (
              <Card key={log.id} className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-gray-100 rounded-lg">
                      <Shield className="w-4 h-4 text-gray-500" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <Badge variant={actionColor(log.action) as any}>
                          {log.action}
                        </Badge>
                        <span className="text-sm text-gray-600">
                          {log.resource_type}
                          {log.resource_id && (
                            <span className="text-gray-400 font-mono ml-1">
                              {log.resource_id.slice(0, 8)}
                            </span>
                          )}
                        </span>
                      </div>
                      {log.detail && (
                        <p className="text-xs text-gray-400 mt-1">{log.detail}</p>
                      )}
                    </div>
                  </div>
                  <span className="text-xs text-gray-400">
                    {new Date(log.created_at).toLocaleString()}
                  </span>
                </div>
              </Card>
            ))}
            <Pagination page={page} totalPages={totalPages} onPageChange={setPage} />
          </div>
        )}
      </div>
    </>
  );
}
