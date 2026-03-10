import type { CropAdvisoryCardData } from "../../lib/api";

type CropAdvisoryCardProps = CropAdvisoryCardData;

function formatValue(value: number | string | undefined) {
  if (value === undefined || value === null || value === "") {
    return "Not available";
  }

  return value;
}

function CropAdvisoryCard({
  crop,
  season,
  sowing_window,
  harvest_window,
  water_requirement,
  estimated_cost,
  expected_yield,
  expected_revenue,
  notes,
}: CropAdvisoryCardProps) {
  return (
    <article className="max-w-xl rounded-2xl border border-emerald-800/60 bg-stone-900/90 p-5 shadow-lg shadow-black/20">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.28em] text-emerald-300/80">
            Crop Advisory
          </p>
          <h3 className="mt-2 text-2xl font-semibold text-stone-50">
            {crop || "Recommended crop"}
          </h3>
        </div>
        <span className="rounded-full border border-emerald-700/60 bg-emerald-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-emerald-200">
          {season || "Season not set"}
        </span>
      </div>

      <div className="mt-5 grid gap-3 text-sm text-stone-300 sm:grid-cols-2">
        <div className="rounded-xl bg-stone-800/80 p-3">
          <p className="text-xs uppercase tracking-wide text-stone-500">Sowing window</p>
          <p className="mt-1 text-base text-stone-100">
            {sowing_window || "Not available"}
          </p>
        </div>
        <div className="rounded-xl bg-stone-800/80 p-3">
          <p className="text-xs uppercase tracking-wide text-stone-500">Harvest window</p>
          <p className="mt-1 text-base text-stone-100">
            {harvest_window || "Not available"}
          </p>
        </div>
      </div>

      <div className="mt-3 rounded-xl bg-stone-800/80 p-3 text-sm text-stone-300">
        <p className="text-xs uppercase tracking-wide text-stone-500">Water requirement</p>
        <p className="mt-1 text-base text-stone-100">
          {water_requirement || "Not available"}
        </p>
      </div>

      <div className="mt-5 grid grid-cols-1 gap-3 text-sm sm:grid-cols-3">
        <div className="rounded-xl border border-stone-800 bg-stone-950/70 p-3">
          <p className="text-xs uppercase tracking-wide text-stone-500">Estimated cost</p>
          <p className="mt-2 text-lg font-semibold text-stone-100">
            {formatValue(estimated_cost)}
          </p>
        </div>
        <div className="rounded-xl border border-stone-800 bg-stone-950/70 p-3">
          <p className="text-xs uppercase tracking-wide text-stone-500">Expected yield</p>
          <p className="mt-2 text-lg font-semibold text-stone-100">
            {formatValue(expected_yield)}
          </p>
        </div>
        <div className="rounded-xl border border-stone-800 bg-stone-950/70 p-3">
          <p className="text-xs uppercase tracking-wide text-stone-500">
            Expected revenue
          </p>
          <p className="mt-2 text-lg font-semibold text-stone-100">
            {formatValue(expected_revenue)}
          </p>
        </div>
      </div>

      <div className="mt-5 rounded-xl border border-dashed border-stone-700/80 bg-stone-950/40 p-4 text-sm leading-6 text-stone-300">
        {notes || "No additional notes available."}
      </div>
    </article>
  );
}

export default CropAdvisoryCard;
