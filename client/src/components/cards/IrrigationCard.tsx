import type { IrrigationCardData } from "../../lib/api";

type IrrigationCardProps = IrrigationCardData;

function IrrigationCard({
  next_watering_date,
  skip_dates,
  expected_rainfall_mm,
  rainfall_date,
  reason,
}: IrrigationCardProps) {
  const normalizedSkipDates = Array.isArray(skip_dates)
    ? skip_dates
    : skip_dates
      ? [skip_dates]
      : [];

  return (
    <article className="max-w-xl rounded-2xl border border-cyan-800/60 bg-stone-900/90 p-5 shadow-lg shadow-black/20">
      <p className="text-xs uppercase tracking-[0.28em] text-cyan-300/80">
        Irrigation Schedule
      </p>
      <h3 className="mt-2 text-xl font-semibold text-stone-50">Next watering date</h3>

      <div className="mt-4 rounded-2xl bg-cyan-500/10 p-5">
        <p className="text-3xl font-semibold text-cyan-100">
          {next_watering_date || "Not available"}
        </p>
      </div>

      {normalizedSkipDates.length ? (
        <div className="mt-4 rounded-xl border border-stone-800 bg-stone-950/60 p-4 text-sm text-stone-200">
          <p className="text-xs uppercase tracking-wide text-stone-500">Skip dates</p>
          <p className="mt-2 leading-6">{normalizedSkipDates.join(", ")}</p>
        </div>
      ) : null}

      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <div className="rounded-xl border border-stone-800 bg-stone-950/60 p-4 text-sm text-stone-200">
          <p className="text-xs uppercase tracking-wide text-stone-500">
            Expected rainfall
          </p>
          <p className="mt-2 text-lg font-semibold">{expected_rainfall_mm ?? "0"} mm</p>
        </div>
        <div className="rounded-xl border border-stone-800 bg-stone-950/60 p-4 text-sm text-stone-200">
          <p className="text-xs uppercase tracking-wide text-stone-500">Rainfall date</p>
          <p className="mt-2 text-lg font-semibold">{rainfall_date || "Not available"}</p>
        </div>
      </div>

      <div className="mt-5 rounded-xl border border-dashed border-stone-700/80 bg-stone-950/40 p-4 text-sm leading-6 text-stone-300">
        {reason || "No reason provided."}
      </div>
    </article>
  );
}

export default IrrigationCard;
