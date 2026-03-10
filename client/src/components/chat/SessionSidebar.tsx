import type { ChatSessionSummary } from "../../lib/api";

interface SessionSidebarProps {
  sessions: ChatSessionSummary[];
  activeSessionId: string | null;
  isLoading: boolean;
  onNewChat: () => void;
  onSelectSession: (sessionId: string) => void;
}

function formatSessionDate(value: string) {
  return new Intl.DateTimeFormat("en-IN", {
    day: "2-digit",
    month: "short",
  }).format(new Date(value));
}

function SessionSidebar({
  sessions,
  activeSessionId,
  isLoading,
  onNewChat,
  onSelectSession,
}: SessionSidebarProps) {
  return (
    <aside className="flex h-full w-full max-w-sm flex-col border-r border-stone-800 bg-stone-950/80">
      <div className="border-b border-stone-800 p-4">
        <button
          type="button"
          onClick={onNewChat}
          className="w-full rounded-xl bg-emerald-500 px-4 py-3 text-sm font-semibold text-emerald-950 transition hover:bg-emerald-400"
        >
          New Chat
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-3">
        {isLoading ? (
          <p className="px-3 py-4 text-sm text-stone-400">Loading sessions...</p>
        ) : sessions.length === 0 ? (
          <p className="px-3 py-4 text-sm text-stone-400">
            No chat history yet. Start a new conversation.
          </p>
        ) : (
          <div className="space-y-2">
            {sessions.map((session) => {
              const isActive = session.id === activeSessionId;

              return (
                <button
                  key={session.id}
                  type="button"
                  onClick={() => onSelectSession(session.id)}
                  className={`w-full rounded-2xl border px-4 py-3 text-left transition ${
                    isActive
                      ? "border-emerald-500/60 bg-emerald-500/10"
                      : "border-stone-800 bg-stone-900 hover:border-stone-700 hover:bg-stone-800/90"
                  }`}
                >
                  <p className="text-sm font-semibold text-stone-100">
                    {session.title || "Untitled conversation"}
                  </p>
                  <p className="mt-2 text-xs uppercase tracking-wide text-stone-500">
                    {formatSessionDate(session.created_at)}
                  </p>
                </button>
              );
            })}
          </div>
        )}
      </div>
    </aside>
  );
}

export default SessionSidebar;
