'use client';

import { useEffect, useState } from 'react';
import Header from '@/components/Header';
import {
  Badge,
  Card,
  CardContent,
  LoadingSpinner,
  StatCard,
  useToast,
} from '@/components/ui';
import { adminApi, AppSettings, User, PaginatedResponse } from '@/lib/api';
import { Settings, Users, Server, Key, Database, Globe } from 'lucide-react';

export default function AdminSettingsPage() {
  const [settings, setSettings] = useState<AppSettings | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAdmin();
  }, []);

  async function loadAdmin() {
    setLoading(true);
    try {
      const [settingsRes, usersRes] = await Promise.allSettled([
        adminApi.getSettings(),
        adminApi.listUsers(1),
      ]);
      if (settingsRes.status === 'fulfilled') setSettings(settingsRes.value);
      if (usersRes.status === 'fulfilled') setUsers(usersRes.value.items);
    } catch (err) {
      console.error('Failed to load admin data:', err);
    } finally {
      setLoading(false);
    }
  }

  if (loading) return <LoadingSpinner />;

  return (
    <>
      <Header title="Admin Settings" subtitle="System configuration and user management" />

      <div className="p-6 space-y-6">
        {/* System Info */}
        {settings && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <StatCard
              label="Environment"
              value={settings.app_env}
              icon={<Server className="w-5 h-5" />}
            />
            <StatCard
              label="Max Upload"
              value={`${settings.max_upload_size_mb} MB`}
              icon={<Database className="w-5 h-5" />}
            />
            <StatCard
              label="LLM Status"
              value={settings.llm_configured ? 'Configured' : 'Not Configured'}
              subtext={settings.langfuse_configured ? 'Langfuse: Active' : 'Langfuse: Inactive'}
              icon={<Key className="w-5 h-5" />}
            />
          </div>
        )}

        {/* Configuration */}
        {settings && (
          <Card>
            <div className="px-6 py-4 border-b border-gray-100">
              <h3 className="text-sm font-semibold text-gray-900">System Configuration</h3>
            </div>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                {Object.entries(settings).map(([key, value]) => (
                  <div key={key} className="flex justify-between items-center py-2 border-b border-gray-50">
                    <span className="text-sm text-gray-600 font-mono">{key}</span>
                    <span className="text-sm text-gray-900">
                      {typeof value === 'boolean' ? (
                        <Badge variant={value ? 'success' : 'default'}>
                          {value ? 'Yes' : 'No'}
                        </Badge>
                      ) : (
                        String(value)
                      )}
                    </span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Users */}
        <Card>
          <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-gray-900">Users</h3>
            <span className="text-xs text-gray-400">{users.length} total</span>
          </div>
          <CardContent className="p-0">
            <table className="w-full">
              <thead>
                <tr className="text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  <th className="px-6 py-3">User</th>
                  <th className="px-6 py-3">Status</th>
                  <th className="px-6 py-3">Role</th>
                  <th className="px-6 py-3">Joined</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {users.map((u) => (
                  <tr key={u.id} className="hover:bg-gray-50">
                    <td className="px-6 py-3">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center text-xs font-medium text-gray-600">
                          {u.full_name?.charAt(0).toUpperCase() || 'U'}
                        </div>
                        <div>
                          <p className="text-sm font-medium text-gray-900">{u.full_name}</p>
                          <p className="text-xs text-gray-400">{u.email}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-3">
                      <Badge variant={u.is_active ? 'success' : 'error'}>
                        {u.is_active ? 'Active' : 'Disabled'}
                      </Badge>
                    </td>
                    <td className="px-6 py-3">
                      <Badge variant={u.is_superuser ? 'info' : 'default'}>
                        {u.is_superuser ? 'Admin' : 'User'}
                      </Badge>
                    </td>
                    <td className="px-6 py-3 text-sm text-gray-400">
                      {new Date(u.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>
      </div>
    </>
  );
}
