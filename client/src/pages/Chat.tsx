import { useEffect, useRef, useState } from "react";
import Spinner from "../components/Spinner";
import { useNavigate } from "react-router-dom";
import ChatInput from "../components/chat/ChatInput";
import ChatMessage from "../components/chat/ChatMessage";
import SessionSidebar from "../components/chat/SessionSidebar";
import {
  getApiErrorMessage,
  getSessionMessages,
  getSessions,
  logout,
  sendMessage,
  type ChatMessage as ChatMessageItem,
  type ChatReply,
  type ChatSessionSummary,
} from "../lib/api";

function sortMessages(messages: ChatMessageItem[]) {
  return [...messages].sort(
    (left, right) =>
      new Date(left.created_at).getTime() - new Date(right.created_at).getTime(),
  );
}

function buildLocalMessage(
  role: "user" | "assistant",
  messageText: string,
  sessionId: string | null,
): ChatMessageItem {
  return {
    id: `${role}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    session_id: sessionId || "pending-session",
    role,
    message_text: messageText,
    message_metadata: null,
    created_at: new Date().toISOString(),
  };
}

function upsertSession(
  sessions: ChatSessionSummary[],
  reply: ChatReply,
  fallbackTitle: string,
): ChatSessionSummary[] {
  const now = new Date().toISOString();
  const nextItem: ChatSessionSummary = {
    id: reply.session_id,
    user_id: sessions.find((session) => session.id === reply.session_id)?.user_id || "",
    title: reply.session_title || fallbackTitle,
    created_at:
      sessions.find((session) => session.id === reply.session_id)?.created_at || now,
    updated_at: now,
  };

  return [
    nextItem,
    ...sessions.filter((session) => session.id !== reply.session_id),
  ];
}

function Chat() {
  const navigate = useNavigate();
  const [sessions, setSessions] = useState<ChatSessionSummary[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessageItem[]>([]);
  const [sessionsLoading, setSessionsLoading] = useState(true);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const endRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadInitialSessions() {
      setSessionsLoading(true);

      try {
        const nextSessions = await getSessions();

        if (cancelled) {
          return;
        }

        setSessions(nextSessions);

        if (!nextSessions[0]) {
          setActiveSessionId(null);
          setMessages([]);
          return;
        }

        setHistoryLoading(true);

        try {
          const detail = await getSessionMessages(nextSessions[0].id);

          if (!cancelled) {
            setActiveSessionId(detail.id);
            setMessages(sortMessages(detail.messages));
          }
        } catch (loadError) {
          if (!cancelled) {
            setError(getApiErrorMessage(loadError));
          }
        } finally {
          if (!cancelled) {
            setHistoryLoading(false);
          }
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(getApiErrorMessage(loadError));
        }
      } finally {
        if (!cancelled) {
          setSessionsLoading(false);
        }
      }
    }

    void loadInitialSessions();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, historyLoading, sending]);

  async function loadSession(sessionId: string) {
    setHistoryLoading(true);
    setError(null);

    try {
      const detail = await getSessionMessages(sessionId);
      setActiveSessionId(detail.id);
      setMessages(sortMessages(detail.messages));
    } catch (loadError) {
      setError(getApiErrorMessage(loadError));
    } finally {
      setHistoryLoading(false);
    }
  }

  function handleNewChat() {
    setActiveSessionId(null);
    setMessages([]);
    setError(null);
  }

  async function handleSend(message: string) {
    const pendingUserMessage = buildLocalMessage("user", message, activeSessionId);

    setMessages((currentMessages) => [...currentMessages, pendingUserMessage]);
    setSending(true);
    setError(null);

    let reply: ChatReply;

    try {
      reply = await sendMessage(activeSessionId, message);
      setActiveSessionId(reply.session_id);
      setSessions((currentSessions) =>
        upsertSession(currentSessions, reply, message.slice(0, 60)),
      );
    } catch (sendError) {
      setMessages((currentMessages) =>
        currentMessages.filter((item) => item.id !== pendingUserMessage.id),
      );
      setError(getApiErrorMessage(sendError));
      setSending(false);
      return;
    }

    try {
      const [detail, refreshedSessions] = await Promise.all([
        getSessionMessages(reply.session_id),
        getSessions(),
      ]);

      setMessages(sortMessages(detail.messages));
      setSessions(refreshedSessions);
      setActiveSessionId(detail.id);
    } catch (refreshError) {
      setMessages((currentMessages) => [
        ...currentMessages,
        buildLocalMessage("assistant", reply.reply, reply.session_id),
      ]);
      setError("Message sent, but chat history could not be refreshed.");
      setSessions((currentSessions) =>
        upsertSession(currentSessions, reply, message.slice(0, 60)),
      );
      if (import.meta.env.DEV) {
        // Keep the original error visible in development tools.
        console.error(refreshError);
      }
    } finally {
      setSending(false);
    }
  }

  async function handleLogout() {
    try {
      await logout();
    } finally {
      navigate("/login", { replace: true });
    }
  }

  return (
    <main className="flex min-h-screen flex-col bg-[radial-gradient(circle_at_top,_rgba(14,165,233,0.10),_transparent_30%),linear-gradient(180deg,_#0c0a09_0%,_#111827_100%)]">
      <header className="border-b border-stone-800 bg-stone-950/80 px-4 py-4 backdrop-blur sm:px-6">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.35em] text-emerald-300/80">
              FarmWise AI
            </p>
            <h1 className="mt-2 text-2xl font-semibold text-stone-50">
              FarmWise Agent
            </h1>
          </div>

          <div className="flex gap-3">
            <button
              type="button"
              onClick={() => navigate("/dashboard")}
              className="rounded-xl border border-stone-700 px-4 py-2 text-sm font-semibold text-stone-200 transition hover:border-stone-500 hover:bg-stone-900"
            >
              Dashboard
            </button>
            <button
              type="button"
              onClick={handleLogout}
              className="rounded-xl bg-emerald-500 px-4 py-2 text-sm font-semibold text-emerald-950 transition hover:bg-emerald-400"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      <div className="mx-auto flex w-full max-w-7xl flex-1 flex-col overflow-hidden px-4 py-6 sm:px-6 lg:flex-row">
        <div className="h-[260px] overflow-hidden rounded-t-3xl border border-stone-800 lg:h-auto lg:w-80 lg:rounded-l-3xl lg:rounded-tr-none">
          <SessionSidebar
            sessions={sessions}
            activeSessionId={activeSessionId}
            isLoading={sessionsLoading}
            onNewChat={handleNewChat}
            onSelectSession={(sessionId) => {
              void loadSession(sessionId);
            }}
          />
        </div>

        <section className="flex min-h-[70vh] flex-1 flex-col rounded-b-3xl border border-t-0 border-stone-800 bg-stone-950/70 lg:rounded-b-none lg:rounded-r-3xl lg:border-l-0 lg:border-t">
          {error ? (
            <div className="border-b border-rose-700/50 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
              {error}
            </div>
          ) : null}

          <div className="flex-1 space-y-4 overflow-y-auto px-4 py-5 sm:px-6">
            {messages.length === 0 && !historyLoading ? (
              <div className="flex h-full items-center justify-center">
                <div className="max-w-lg rounded-3xl border border-dashed border-stone-700 bg-stone-900/70 p-8 text-center">
                  <p className="text-sm uppercase tracking-[0.3em] text-emerald-300/70">
                    New conversation
                  </p>
                  <h2 className="mt-3 text-2xl font-semibold text-stone-50">
                    Ask about your farm conditions
                  </h2>
                  <p className="mt-4 text-sm leading-6 text-stone-400">
                    The backend will forward your region, weather, crop, and mandi
                    price context to the agent service.
                  </p>
                </div>
              </div>
            ) : null}

            {messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))}

            {historyLoading ? (
              <div className="inline-flex items-center gap-2 text-sm text-stone-400">
                <Spinner className="h-4 w-4" />
                <span>Loading conversation...</span>
              </div>
            ) : null}

            {sending ? (
              <div className="flex justify-start">
                <div className="inline-flex items-center gap-3 rounded-2xl border border-stone-800 bg-stone-900 px-4 py-3 text-sm text-stone-300">
                  <Spinner className="h-4 w-4 text-emerald-300" />
                  <span>FarmWise Agent is thinking...</span>
                </div>
              </div>
            ) : null}

            <div ref={endRef} />
          </div>

          <ChatInput disabled={sending} loading={sending} onSend={handleSend} />
        </section>
      </div>
    </main>
  );
}

export default Chat;
