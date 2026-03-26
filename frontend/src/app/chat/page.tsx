'use client';

import { useEffect, useRef, useState } from 'react';
import Header from '@/components/Header';
import { Button, Badge, EmptyState, LoadingSpinner } from '@/components/ui';
import { chatApi, ChatRequest, ChatResponse, Conversation, Message } from '@/lib/api';
import { useAuthStore } from '@/stores/auth';
import {
  Send,
  Plus,
  MessageSquare,
  FileText,
  Bot,
  User as UserIcon,
  Zap,
  Trash2,
  ExternalLink,
  Clock,
} from 'lucide-react';

export default function ChatPage() {
  const { user } = useAuthStore();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [useRetrieval, setUseRetrieval] = useState(true);
  const [useAgent, setUseAgent] = useState(false);
  const [lastResponse, setLastResponse] = useState<ChatResponse | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Default workspace - in production, this would be from a workspace selector
  const workspaceId = '00000000-0000-0000-0000-000000000001';

  useEffect(() => {
    loadConversations();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  async function loadConversations() {
    try {
      const res = await chatApi.listConversations(workspaceId);
      setConversations(res.items);
    } catch (err) {
      console.error('Failed to load conversations:', err);
    }
  }

  async function loadConversation(id: string) {
    try {
      const detail = await chatApi.getConversation(id);
      setActiveConversationId(id);
      setMessages(detail.messages || []);
    } catch (err) {
      console.error('Failed to load conversation:', err);
    }
  }

  function startNewChat() {
    setActiveConversationId(null);
    setMessages([]);
    setLastResponse(null);
    inputRef.current?.focus();
  }

  async function handleSend() {
    if (!input.trim() || sending) return;

    const userMessage = input.trim();
    setInput('');
    setSending(true);

    // Optimistic: add user message instantly
    setMessages((prev) => [
      ...prev,
      {
        id: `temp-${Date.now()}`,
        role: 'user',
        content: userMessage,
        token_count: 0,
        created_at: new Date().toISOString(),
      },
    ]);

    try {
      const request: ChatRequest = {
        message: userMessage,
        workspace_id: workspaceId,
        conversation_id: activeConversationId || undefined,
        use_retrieval: useRetrieval,
        use_agent: useAgent,
      };

      const response = await chatApi.send(request);
      setLastResponse(response);

      if (!activeConversationId) {
        setActiveConversationId(response.conversation_id);
        loadConversations();
      }

      // Add assistant message
      setMessages((prev) => [
        ...prev,
        {
          id: response.message_id,
          role: 'assistant',
          content: response.content,
          citations: response.citations,
          tool_calls: response.tool_calls,
          token_count: response.token_count,
          latency_ms: response.latency_ms,
          model_name: response.model_name,
          created_at: new Date().toISOString(),
        },
      ]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: `error-${Date.now()}`,
          role: 'assistant',
          content: `Error: ${err.error || 'Failed to send message'}`,
          token_count: 0,
          created_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setSending(false);
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-screen">
      <Header
        title="Chat"
        subtitle="Ask questions against your knowledge base"
        actions={
          <div className="flex items-center gap-2">
            <label className="flex items-center gap-1.5 text-xs text-gray-500">
              <input
                type="checkbox"
                checked={useRetrieval}
                onChange={(e) => setUseRetrieval(e.target.checked)}
                className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              />
              RAG
            </label>
            <label className="flex items-center gap-1.5 text-xs text-gray-500">
              <input
                type="checkbox"
                checked={useAgent}
                onChange={(e) => setUseAgent(e.target.checked)}
                className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              />
              Agent
            </label>
          </div>
        }
      />

      <div className="flex flex-1 overflow-hidden">
        {/* Conversation sidebar */}
        {sidebarOpen && (
          <div className="w-72 bg-white border-r border-gray-200 flex flex-col">
            <div className="p-3 border-b border-gray-100">
              <Button
                variant="primary"
                size="sm"
                className="w-full"
                onClick={startNewChat}
              >
                <Plus className="w-4 h-4" /> New Chat
              </Button>
            </div>
            <div className="flex-1 overflow-y-auto">
              {conversations.length > 0 ? (
                conversations.map((conv) => (
                  <button
                    key={conv.id}
                    onClick={() => loadConversation(conv.id)}
                    className={`w-full text-left px-4 py-3 border-b border-gray-50 hover:bg-gray-50 transition-colors ${
                      activeConversationId === conv.id ? 'bg-primary-50 border-l-2 border-l-primary-500' : ''
                    }`}
                  >
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {conv.title || 'Untitled'}
                    </p>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-xs text-gray-400">
                        {conv.message_count} msgs
                      </span>
                      <span className="text-xs text-gray-400">
                        {new Date(conv.updated_at).toLocaleDateString()}
                      </span>
                    </div>
                  </button>
                ))
              ) : (
                <div className="p-4 text-center text-sm text-gray-400">
                  No conversations yet
                </div>
              )}
            </div>
          </div>
        )}

        {/* Chat area */}
        <div className="flex-1 flex flex-col">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
            {messages.length === 0 ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <Bot className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900">Start a conversation</h3>
                  <p className="text-sm text-gray-500 mt-1 max-w-sm">
                    Ask questions about your knowledge base. Enable RAG for document-grounded
                    answers or Agent mode for tool-augmented responses.
                  </p>
                </div>
              </div>
            ) : (
              messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : ''}`}
                >
                  {msg.role !== 'user' && (
                    <div className="w-8 h-8 bg-primary-100 rounded-lg flex items-center justify-center flex-shrink-0">
                      <Bot className="w-4 h-4 text-primary-600" />
                    </div>
                  )}
                  <div
                    className={`max-w-[70%] ${
                      msg.role === 'user'
                        ? 'bg-primary-600 text-white rounded-2xl rounded-br-md px-4 py-3'
                        : 'bg-white border border-gray-200 rounded-2xl rounded-bl-md px-4 py-3'
                    }`}
                  >
                    <p className="text-sm whitespace-pre-wrap">{msg.content}</p>

                    {/* Citations */}
                    {msg.citations && msg.citations.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-gray-100 space-y-2">
                        <p className="text-xs font-medium text-gray-500">Sources</p>
                        {msg.citations.map((cite: any, i: number) => (
                          <div
                            key={i}
                            className="flex items-start gap-2 bg-gray-50 rounded-lg p-2"
                          >
                            <FileText className="w-3 h-3 text-gray-400 mt-0.5 flex-shrink-0" />
                            <div>
                              <p className="text-xs font-medium text-gray-700">
                                {cite.document_title}
                              </p>
                              <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">
                                {cite.content_snippet}
                              </p>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Tool calls */}
                    {msg.tool_calls && msg.tool_calls.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {msg.tool_calls.map((tc: any, i: number) => (
                          <Badge key={i} variant="info">
                            <Zap className="w-3 h-3 mr-1" />
                            {tc.name || tc.tool}
                          </Badge>
                        ))}
                      </div>
                    )}

                    {/* Metadata */}
                    {msg.role === 'assistant' && msg.token_count > 0 && (
                      <div className="mt-2 flex items-center gap-3 text-xs text-gray-400">
                        {msg.model_name && <span>{msg.model_name}</span>}
                        <span>{msg.token_count} tokens</span>
                        {msg.latency_ms && <span>{msg.latency_ms}ms</span>}
                      </div>
                    )}
                  </div>
                  {msg.role === 'user' && (
                    <div className="w-8 h-8 bg-gray-200 rounded-lg flex items-center justify-center flex-shrink-0">
                      <UserIcon className="w-4 h-4 text-gray-600" />
                    </div>
                  )}
                </div>
              ))
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Response meta bar */}
          {lastResponse && (
            <div className="px-6 py-2 bg-gray-50 border-t border-gray-100 flex items-center gap-4 text-xs text-gray-400">
              {lastResponse.model_name && (
                <span>Model: {lastResponse.model_name}</span>
              )}
              <span>{lastResponse.token_count} tokens</span>
              <span>{lastResponse.latency_ms}ms</span>
              {lastResponse.fallback_used && (
                <Badge variant="warning">Fallback</Badge>
              )}
              {lastResponse.trace_id && (
                <a
                  href={`/traces`}
                  className="text-primary-500 hover:text-primary-600 flex items-center gap-1"
                >
                  <ExternalLink className="w-3 h-3" /> Trace
                </a>
              )}
            </div>
          )}

          {/* Input area */}
          <div className="border-t border-gray-200 bg-white p-4">
            <div className="flex items-end gap-3 max-w-4xl mx-auto">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask a question..."
                rows={1}
                className="flex-1 resize-none border border-gray-300 rounded-xl px-4 py-3 text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none max-h-32"
                style={{ minHeight: '44px' }}
              />
              <Button
                onClick={handleSend}
                disabled={!input.trim() || sending}
                loading={sending}
                className="rounded-xl"
              >
                <Send className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
