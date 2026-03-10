import type {
  ChatMessage as ChatMessageItem,
  CropAdvisoryCardData,
  IrrigationCardData,
  MarketTimingCardData,
  PestDiagnosisCardData,
} from "../../lib/api";
import CropAdvisoryCard from "../cards/CropAdvisoryCard";
import IrrigationCard from "../cards/IrrigationCard";
import MarketTimingCard from "../cards/MarketTimingCard";
import PestDiagnosisCard from "../cards/PestDiagnosisCard";

interface ChatMessageProps {
  message: ChatMessageItem;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function AssistantCard({ message }: { message: ChatMessageItem }) {
  const metadata = message.message_metadata;

  if (!metadata?.structured || !metadata.intent || !isRecord(metadata.data)) {
    return (
      <div className="max-w-xl rounded-2xl border border-stone-800 bg-stone-900 px-4 py-3 text-sm leading-6 text-stone-200">
        {message.message_text}
      </div>
    );
  }

  switch (metadata.intent) {
    case "crop_recommendation":
      return <CropAdvisoryCard {...(metadata.data as CropAdvisoryCardData)} />;
    case "pest_diagnosis":
      return <PestDiagnosisCard {...(metadata.data as PestDiagnosisCardData)} />;
    case "market_timing":
      return <MarketTimingCard {...(metadata.data as MarketTimingCardData)} />;
    case "irrigation_schedule":
      return <IrrigationCard {...(metadata.data as IrrigationCardData)} />;
    default:
      return (
        <div className="max-w-xl rounded-2xl border border-stone-800 bg-stone-900 px-4 py-3 text-sm leading-6 text-stone-200">
          {message.message_text}
        </div>
      );
  }
}

function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      {isUser ? (
        <div className="max-w-xl rounded-2xl bg-emerald-500 px-4 py-3 text-sm leading-6 text-emerald-950 shadow-lg shadow-emerald-900/20">
          {message.message_text}
        </div>
      ) : (
        <AssistantCard message={message} />
      )}
    </div>
  );
}

export default ChatMessage;
