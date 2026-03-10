import type { MandiPrice } from "../../lib/api";

interface PriceWidgetProps {
  prices: MandiPrice[];
}

function formatRecordedDate(value: string) {
  return new Intl.DateTimeFormat("en-IN", {
    day: "2-digit",
    month: "short",
  }).format(new Date(value));
}

function PriceWidget({ prices }: PriceWidgetProps) {
  return (
    <section className="rounded-3xl border border-stone-800 bg-stone-900/90 p-5 shadow-xl shadow-black/20">
      <p className="text-xs uppercase tracking-[0.28em] text-sky-300/80">Mandi prices</p>
      <h2 className="mt-2 text-xl font-semibold text-stone-50">Today&apos;s market</h2>

      <div className="mt-5 space-y-3">
        {prices.length === 0 ? (
          <p className="rounded-2xl border border-dashed border-stone-700 p-4 text-sm text-stone-400">
            No mandi price data available.
          </p>
        ) : (
          prices.map((price) => (
            <div
              key={price.id}
              className="rounded-2xl border border-stone-800 bg-stone-950/70 px-4 py-3"
            >
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-sm font-semibold text-stone-100">{price.crop_name}</p>
                  <p className="mt-1 text-xs uppercase tracking-wide text-stone-500">
                    {formatRecordedDate(price.recorded_date)}
                  </p>
                </div>
                <p className="text-lg font-semibold text-sky-200">
                  ₹{price.price_per_quintal}/qtl
                </p>
              </div>
            </div>
          ))
        )}
      </div>
    </section>
  );
}

export default PriceWidget;
