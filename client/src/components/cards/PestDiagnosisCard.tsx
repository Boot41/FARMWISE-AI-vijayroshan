import type { PestDiagnosisCardData } from "../../lib/api";

type PestDiagnosisCardProps = PestDiagnosisCardData;

function PestDiagnosisCard({
  pest_name,
  crop,
  symptoms,
  treatment,
  dosage,
  frequency,
  organic_alternative,
  warning,
}: PestDiagnosisCardProps) {
  return (
    <article className="max-w-xl rounded-2xl border border-amber-700/60 bg-stone-900/90 p-5 shadow-lg shadow-black/20">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.28em] text-amber-300/80">
            Pest Diagnosis
          </p>
          <h3 className="mt-2 text-2xl font-semibold text-amber-100">
            {pest_name || "Unidentified issue"}
          </h3>
        </div>
        <span className="rounded-full border border-amber-700/60 bg-amber-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-amber-100">
          {crop || "Crop not set"}
        </span>
      </div>

      <div className="mt-5 rounded-xl bg-stone-800/80 p-4">
        <p className="text-xs uppercase tracking-wide text-stone-500">Symptoms</p>
        <p className="mt-2 text-sm leading-6 text-stone-200">
          {symptoms || "No symptom details available."}
        </p>
      </div>

      <div className="mt-4 grid gap-3 text-sm text-stone-200 sm:grid-cols-3">
        <div className="rounded-xl border border-stone-800 bg-stone-950/70 p-3">
          <p className="text-xs uppercase tracking-wide text-stone-500">Treatment</p>
          <p className="mt-2 leading-6">{treatment || "Not available"}</p>
        </div>
        <div className="rounded-xl border border-stone-800 bg-stone-950/70 p-3">
          <p className="text-xs uppercase tracking-wide text-stone-500">Dosage</p>
          <p className="mt-2 leading-6">{dosage || "Not available"}</p>
        </div>
        <div className="rounded-xl border border-stone-800 bg-stone-950/70 p-3">
          <p className="text-xs uppercase tracking-wide text-stone-500">Frequency</p>
          <p className="mt-2 leading-6">{frequency || "Not available"}</p>
        </div>
      </div>

      {organic_alternative ? (
        <div className="mt-4 rounded-xl border border-emerald-800/70 bg-emerald-500/10 p-4 text-sm leading-6 text-emerald-100">
          Organic alternative: {organic_alternative}
        </div>
      ) : null}

      {warning ? (
        <div className="mt-4 rounded-xl border border-amber-700/60 bg-amber-500/10 p-4 text-sm leading-6 text-amber-100">
          Warning: {warning}
        </div>
      ) : null}
    </article>
  );
}

export default PestDiagnosisCard;
