import type { RegionCrop } from "../../lib/api";

interface RegionCropsWidgetProps {
  crops: RegionCrop[];
}

function RegionCropsWidget({ crops }: RegionCropsWidgetProps) {
  return (
    <section className="rounded-3xl border border-stone-800 bg-stone-900/90 p-5 shadow-xl shadow-black/20">
      <p className="text-xs uppercase tracking-[0.28em] text-amber-300/80">
        Region crops
      </p>
      <h2 className="mt-2 text-xl font-semibold text-stone-50">Suitable crops</h2>

      <div className="mt-5 space-y-4">
        {crops.length === 0 ? (
          <p className="rounded-2xl border border-dashed border-stone-700 p-4 text-sm text-stone-400">
            No crop suitability data available.
          </p>
        ) : (
          crops.map((crop) => (
            <div
              key={crop.id}
              className="rounded-2xl border border-stone-800 bg-stone-950/70 px-4 py-3"
            >
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-sm font-semibold text-stone-100">{crop.crop_name}</p>
                  <p className="mt-1 text-xs uppercase tracking-wide text-stone-500">
                    {crop.crop_season}
                  </p>
                </div>
                <p className="text-sm font-semibold text-amber-200">
                  {Math.round(crop.suitability_score * 100)}%
                </p>
              </div>

              <div className="mt-3 h-2 rounded-full bg-stone-800">
                <div
                  className="h-2 rounded-full bg-gradient-to-r from-amber-400 to-emerald-400"
                  style={{
                    width: `${Math.max(8, Math.min(crop.suitability_score * 100, 100))}%`,
                  }}
                />
              </div>
            </div>
          ))
        )}
      </div>
    </section>
  );
}

export default RegionCropsWidget;
