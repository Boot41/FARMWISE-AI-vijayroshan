import type { WeatherForecast } from "../../lib/api";

interface WeatherWidgetProps {
  forecasts: WeatherForecast[];
}

function formatDay(value: string) {
  return new Intl.DateTimeFormat("en-IN", {
    weekday: "short",
    day: "numeric",
    month: "short",
  }).format(new Date(value));
}

function WeatherWidget({ forecasts }: WeatherWidgetProps) {
  return (
    <section className="rounded-3xl border border-stone-800 bg-stone-900/90 p-5 shadow-xl shadow-black/20">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.28em] text-emerald-300/80">
            Weather
          </p>
          <h2 className="mt-2 text-xl font-semibold text-stone-50">7 day forecast</h2>
        </div>
        <span className="rounded-full border border-stone-700 px-3 py-1 text-xs text-stone-300">
          Local region
        </span>
      </div>

      <div className="mt-5 space-y-3">
        {forecasts.length === 0 ? (
          <p className="rounded-2xl border border-dashed border-stone-700 p-4 text-sm text-stone-400">
            No weather forecast data available.
          </p>
        ) : (
          forecasts.map((forecast) => (
            <div
              key={forecast.id}
              className="grid grid-cols-[1.2fr,1fr,1fr,1fr] gap-3 rounded-2xl border border-stone-800 bg-stone-950/70 px-4 py-3 text-sm"
            >
              <div>
                <p className="font-semibold text-stone-100">
                  {formatDay(forecast.forecast_date)}
                </p>
              </div>
              <div>
                <p className="text-xs uppercase tracking-wide text-stone-500">Max temp</p>
                <p className="mt-1 text-stone-100">{forecast.max_temp}°C</p>
              </div>
              <div>
                <p className="text-xs uppercase tracking-wide text-stone-500">Rainfall</p>
                <p className="mt-1 text-stone-100">
                  {forecast.expected_rainfall_mm} mm{" "}
                  {forecast.expected_rainfall_mm > 5 ? (
                    <span className="ml-1" aria-label="rain expected">
                      🌧
                    </span>
                  ) : null}
                </p>
              </div>
              <div>
                <p className="text-xs uppercase tracking-wide text-stone-500">Humidity</p>
                <p className="mt-1 text-stone-100">{forecast.humidity_pct}%</p>
              </div>
            </div>
          ))
        )}
      </div>
    </section>
  );
}

export default WeatherWidget;
