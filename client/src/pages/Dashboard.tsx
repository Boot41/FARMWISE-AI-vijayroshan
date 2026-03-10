import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import PriceWidget from "../components/dashboard/PriceWidget";
import RegionCropsWidget from "../components/dashboard/RegionCropsWidget";
import WeatherWidget from "../components/dashboard/WeatherWidget";
import {
  getApiErrorMessage,
  getMe,
  getPrices,
  getRegionCrops,
  getWeather,
  logout,
  type MandiPrice,
  type RegionCrop,
  type UserProfile,
  type WeatherForecast,
} from "../lib/api";

function Dashboard() {
  const navigate = useNavigate();
  const [user, setUser] = useState<UserProfile | null>(null);
  const [weather, setWeather] = useState<WeatherForecast[]>([]);
  const [prices, setPrices] = useState<MandiPrice[]>([]);
  const [crops, setCrops] = useState<RegionCrop[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [loggingOut, setLoggingOut] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function loadDashboard() {
      setLoading(true);
      setError(null);

      try {
        const profile = await getMe();

        if (cancelled) {
          return;
        }

        setUser(profile);

        const [weatherData, priceData, cropData] = await Promise.all([
          getWeather(profile.region_id),
          getPrices(profile.region_id),
          getRegionCrops(profile.region_id),
        ]);

        if (!cancelled) {
          setWeather(weatherData);
          setPrices(priceData);
          setCrops(cropData);
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(getApiErrorMessage(loadError));
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadDashboard();

    return () => {
      cancelled = true;
    };
  }, []);

  async function handleLogout() {
    setLoggingOut(true);

    try {
      await logout();
    } finally {
      navigate("/login", { replace: true });
    }
  }

  const tickerItems = prices.map(
    (price) => `🌾 ${price.crop_name} ₹${price.price_per_quintal}/qtl`,
  );
  const tickerText = tickerItems.join("  |  ");

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(16,185,129,0.12),_transparent_30%),linear-gradient(180deg,_#0c0a09_0%,_#111827_100%)]">
      <div className="mx-auto flex min-h-screen max-w-7xl flex-col px-4 py-6 sm:px-6 lg:px-8">
        <header className="rounded-3xl border border-stone-800 bg-stone-950/70 p-6 shadow-2xl shadow-black/20 backdrop-blur">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.35em] text-emerald-300/80">
                FarmWise AI
              </p>
              <h1 className="mt-3 text-3xl font-semibold text-stone-50">
                Welcome{user ? `, ${user.name}` : ""}
              </h1>
              <p className="mt-3 text-sm leading-6 text-stone-400">
                {user
                  ? `${user.region.region_name}, ${user.region.district}, ${user.region.state}`
                  : "Loading your region context..."}
              </p>
            </div>

            <div className="flex flex-col gap-3 sm:flex-row">
              <button
                type="button"
                onClick={() => navigate("/chat")}
                className="rounded-2xl bg-emerald-500 px-5 py-3 text-sm font-semibold text-emerald-950 transition hover:bg-emerald-400"
              >
                Ask FarmWise Agent →
              </button>
              <button
                type="button"
                onClick={handleLogout}
                disabled={loggingOut}
                className="rounded-2xl border border-stone-700 px-5 py-3 text-sm font-semibold text-stone-200 transition hover:border-stone-500 hover:bg-stone-900 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {loggingOut ? "Logging out..." : "Logout"}
              </button>
            </div>
          </div>
        </header>

        {error ? (
          <div className="mt-6 rounded-2xl border border-rose-700/60 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
            {error}
          </div>
        ) : null}

        {loading ? (
          <div className="mt-6 rounded-3xl border border-stone-800 bg-stone-950/70 p-10 text-center text-sm text-stone-400">
            Loading dashboard data...
          </div>
        ) : (
          <>
            <section className="mt-6 grid gap-6 xl:grid-cols-3">
              <WeatherWidget forecasts={weather} />
              <PriceWidget prices={prices} />
              <RegionCropsWidget crops={crops} />
            </section>

            <section className="mt-6 overflow-hidden rounded-2xl border border-stone-800 bg-stone-950/80">
              <div className="flex h-12 items-center overflow-hidden whitespace-nowrap text-sm text-stone-300">
                {tickerText ? (
                  <div className="ticker-track flex items-center">
                    <span className="px-6">{tickerText}</span>
                    <span className="px-6" aria-hidden="true">
                      {tickerText}
                    </span>
                  </div>
                ) : (
                  <span className="px-4 text-stone-500">
                    Mandi price ticker will appear when price data is available.
                  </span>
                )}
              </div>
            </section>
          </>
        )}
      </div>
    </main>
  );
}

export default Dashboard;
