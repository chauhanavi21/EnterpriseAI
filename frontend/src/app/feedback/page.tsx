'use client';

import { useEffect, useState } from 'react';
import Header from '@/components/Header';
import {
  Badge,
  Card,
  EmptyState,
  LoadingSpinner,
  Pagination,
  StatCard,
  useToast,
} from '@/components/ui';
import { feedbackApi, Feedback, FeedbackStats, PaginatedResponse } from '@/lib/api';
import { ThumbsUp, ThumbsDown, Tag, MessageSquare, TrendingUp, BarChart3 } from 'lucide-react';

export default function FeedbackPage() {
  const [feedbacks, setFeedbacks] = useState<Feedback[]>([]);
  const [stats, setStats] = useState<FeedbackStats | null>(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, [page]);

  async function loadData() {
    setLoading(true);
    try {
      const [fbRes, statsRes] = await Promise.allSettled([
        feedbackApi.list(page),
        feedbackApi.stats(),
      ]);
      if (fbRes.status === 'fulfilled') {
        setFeedbacks(fbRes.value.items);
        setTotalPages(fbRes.value.total_pages);
      }
      if (statsRes.status === 'fulfilled') {
        setStats(statsRes.value);
      }
    } catch (err) {
      console.error('Failed to load feedback:', err);
    } finally {
      setLoading(false);
    }
  }

  const satisfactionRate =
    stats && stats.total > 0
      ? Math.round((stats.thumbs_up / stats.total) * 100)
      : 0;

  return (
    <>
      <Header title="Feedback" subtitle="User satisfaction and feedback analytics" />

      <div className="p-6 space-y-6">
        {/* Stats */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <StatCard
              label="Total Feedback"
              value={stats.total}
              icon={<MessageSquare className="w-5 h-5" />}
            />
            <StatCard
              label="Positive"
              value={stats.thumbs_up}
              subtext={`${satisfactionRate}% of total`}
              icon={<ThumbsUp className="w-5 h-5" />}
            />
            <StatCard
              label="Negative"
              value={stats.thumbs_down}
              subtext={`${100 - satisfactionRate}% of total`}
              icon={<ThumbsDown className="w-5 h-5" />}
            />
            <StatCard
              label="Satisfaction"
              value={`${satisfactionRate}%`}
              icon={<TrendingUp className="w-5 h-5" />}
            />
          </div>
        )}

        {/* Top tags */}
        {stats && stats.top_tags && stats.top_tags.length > 0 && (
          <Card className="p-5">
            <h3 className="text-sm font-medium text-gray-900 mb-3">Top Tags</h3>
            <div className="flex flex-wrap gap-2">
              {stats.top_tags.map((t) => (
                <span
                  key={t.tag}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-gray-100 rounded-full text-sm text-gray-700"
                >
                  <Tag className="w-3 h-3" />
                  {t.tag}
                  <span className="text-xs text-gray-400">({t.count})</span>
                </span>
              ))}
            </div>
          </Card>
        )}

        {/* Feedback list */}
        {loading ? (
          <LoadingSpinner />
        ) : feedbacks.length === 0 ? (
          <EmptyState
            icon={<ThumbsUp className="w-12 h-12 text-gray-300" />}
            title="No feedback yet"
            description="Feedback will appear here when users rate chat responses"
          />
        ) : (
          <div className="space-y-2">
            {feedbacks.map((fb) => (
              <Card key={fb.id} className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    <div
                      className={`p-2 rounded-lg ${
                        fb.rating === 'thumbs_up'
                          ? 'bg-green-100'
                          : 'bg-red-100'
                      }`}
                    >
                      {fb.rating === 'thumbs_up' ? (
                        <ThumbsUp className="w-4 h-4 text-green-600" />
                      ) : (
                        <ThumbsDown className="w-4 h-4 text-red-600" />
                      )}
                    </div>
                    <div>
                      {fb.comment && (
                        <p className="text-sm text-gray-900">{fb.comment}</p>
                      )}
                      {fb.tags && fb.tags.length > 0 && (
                        <div className="flex gap-1 mt-1.5">
                          {fb.tags.map((tag) => (
                            <Badge key={tag} variant="default">{tag}</Badge>
                          ))}
                        </div>
                      )}
                      <p className="text-xs text-gray-400 mt-1">
                        Message: {fb.message_id.slice(0, 8)}...
                      </p>
                    </div>
                  </div>
                  <span className="text-xs text-gray-400">
                    {new Date(fb.created_at).toLocaleString()}
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
