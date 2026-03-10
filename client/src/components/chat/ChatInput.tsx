import { useEffect, useRef, useState, type ChangeEvent, type KeyboardEvent } from "react";
import Spinner from "../Spinner";

interface ChatInputProps {
  disabled: boolean;
  loading: boolean;
  onSend: (message: string) => Promise<void> | void;
}

function ChatInput({ disabled, loading, onSend }: ChatInputProps) {
  const [message, setMessage] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  useEffect(() => {
    const textarea = textareaRef.current;

    if (!textarea) {
      return;
    }

    textarea.style.height = "0px";
    textarea.style.height = `${Math.min(textarea.scrollHeight, 120)}px`;
  }, [message]);

  async function submitMessage() {
    const trimmedMessage = message.trim();

    if (!trimmedMessage || disabled) {
      return;
    }

    setMessage("");
    await onSend(trimmedMessage);
  }

  function handleChange(event: ChangeEvent<HTMLTextAreaElement>) {
    setMessage(event.target.value);
  }

  async function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      await submitMessage();
    }
  }

  return (
    <div className="border-t border-stone-800 bg-stone-950/90 p-4">
      <div className="flex items-end gap-3 rounded-2xl border border-stone-800 bg-stone-900 p-3">
        <textarea
          ref={textareaRef}
          value={message}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          rows={1}
          disabled={disabled}
          placeholder="Ask about crops, pests, prices, or irrigation..."
          className="max-h-[120px] min-h-[48px] flex-1 resize-none bg-transparent px-1 py-2 text-sm text-stone-100 outline-none placeholder:text-stone-500 disabled:cursor-not-allowed"
        />
        <button
          type="button"
          onClick={submitMessage}
          disabled={disabled || !message.trim()}
          className="inline-flex min-w-[96px] items-center justify-center gap-2 rounded-xl bg-emerald-500 px-4 py-3 text-sm font-semibold text-emerald-950 transition hover:bg-emerald-400 disabled:cursor-not-allowed disabled:bg-stone-700 disabled:text-stone-400"
        >
          {loading ? (
            <>
              <Spinner className="h-4 w-4" />
              <span>Sending</span>
            </>
          ) : (
            "Send"
          )}
        </button>
      </div>
    </div>
  );
}

export default ChatInput;
