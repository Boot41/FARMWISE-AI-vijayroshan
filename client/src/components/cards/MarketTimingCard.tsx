import type { MarketTimingCardData } from "../../lib/api";

type MarketTimingCardProps = MarketTimingCardData;

function formatPrice(value: number | string | undefined, unit: string | undefined) {
  if (value === undefined || value === null || value === "") {
    return "Not available";
  }

  return `₹${value}${unit ? ` / ${unit}` : ""}`;
}

function MarketTimingCard({
  crop,
  current_price,
  price_unit,
  trend,
  trend_pct,
  advice,
}: MarketTimingCardProps) {
  const isUp = String(trend || "").toLowerCase().includes("up");
  const trendArrow = isUp ? "↑" : "↓";

  return (
    <article className="max-w-xl rounded-2xl border border-sky-800/60 bg-stone-900/90 p-5 shadow-lg shadow-black/20">
      <p className="text-xs uppercase tracking-[0.28em] text-sky-300/80">Market Timing</p>
      <h3 className="mt-2 text-2xl font-semibold text-stone-50">
        {crop || "Market update"}
      </h3>

      <div className="mt-5 rounded-2xl bg-sky-500/10 p-5">
        <p className="text-xs uppercase tracking-wide text-sky-200/70">Current price</p>
        <p className="mt-2 text-3xl font-semibold text-sky-100">
          {formatPrice(current_price, price_unit)}
        </p>
      </div>

      <div className="mt-4 inline-flex items-center gap-2 rounded-full border border-stone-700 bg-stone-950/70 px-4 py-2 text-sm text-stone-200">
        <span
          className={
            isUp ? "text-emerald-300" : "text-rose-300"
          }
        >
          {trendArrow}
        </span>
        <span className="capitalize">{trend || "Trend unavailable"}</span>
        <span className="text-stone-500">•</span>
        <span>{trend_pct ?? "0"}%</span>
      </div>

      <div className="mt-5 rounded-xl border border-dashed border-stone-700/80 bg-stone-950/40 p-4 text-sm leading-6 text-stone-300">
        {advice || "No advice available."}
      </div>
    </article>
  );
}

export default MarketTimingCard;
