import { useEffect, useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import {
  getApiErrorMessage,
  getRegions,
  login,
  register,
  type Region,
} from "../lib/api";
import { setTokens } from "../lib/auth";

type AuthMode = "login" | "register";

function Login() {
  const navigate = useNavigate();
  const [mode, setMode] = useState<AuthMode>("login");
  const [regions, setRegions] = useState<Region[]>([]);
  const [regionsLoading, setRegionsLoading] = useState(true);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [regionId, setRegionId] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadRegions() {
      setRegionsLoading(true);

      try {
        const regionOptions = await getRegions();

        if (!cancelled) {
          setRegions(regionOptions);
          setRegionId((currentRegionId) => currentRegionId || regionOptions[0]?.id || "");
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(getApiErrorMessage(loadError));
        }
      } finally {
        if (!cancelled) {
          setRegionsLoading(false);
        }
      }
    }

    void loadRegions();

    return () => {
      cancelled = true;
    };
  }, []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      const payload =
        mode === "login"
          ? await login(email, password)
          : await register(name, email, password, phone.trim() || null, regionId);

      setTokens(payload.tokens.access_token, payload.tokens.refresh_token);
      navigate("/dashboard", { replace: true });
    } catch (submitError) {
      setError(getApiErrorMessage(submitError));
    } finally {
      setSubmitting(false);
    }
  }

  function toggleMode() {
    setError(null);
    setMode((currentMode) => (currentMode === "login" ? "register" : "login"));
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-[radial-gradient(circle_at_top,_rgba(16,185,129,0.18),_transparent_30%),linear-gradient(180deg,_#0c0a09_0%,_#111827_100%)] px-4 py-10">
      <div className="w-full max-w-md rounded-3xl border border-stone-800 bg-stone-950/90 p-8 shadow-2xl shadow-black/30 backdrop-blur">
        <div className="text-center">
          <p className="text-xs uppercase tracking-[0.35em] text-emerald-300/80">
            FarmWise AI
          </p>
          <h1 className="mt-3 text-3xl font-semibold text-stone-50">
            {mode === "login" ? "Sign in" : "Create account"}
          </h1>
          <p className="mt-3 text-sm leading-6 text-stone-400">
            Clean access to region data, mandi prices, weather, and the FarmWise
            agent.
          </p>
        </div>

        <form className="mt-8 space-y-4" onSubmit={handleSubmit}>
          {mode === "register" ? (
            <label className="block">
              <span className="mb-2 block text-sm font-medium text-stone-300">Name</span>
              <input
                value={name}
                onChange={(event) => setName(event.target.value)}
                required
                className="w-full rounded-2xl border border-stone-800 bg-stone-900 px-4 py-3 text-sm text-stone-100 outline-none transition focus:border-emerald-500"
                placeholder="Farmer name"
              />
            </label>
          ) : null}

          <label className="block">
            <span className="mb-2 block text-sm font-medium text-stone-300">Email</span>
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
              className="w-full rounded-2xl border border-stone-800 bg-stone-900 px-4 py-3 text-sm text-stone-100 outline-none transition focus:border-emerald-500"
              placeholder="name@example.com"
            />
          </label>

          {mode === "register" ? (
            <label className="block">
              <span className="mb-2 block text-sm font-medium text-stone-300">
                Phone (optional)
              </span>
              <input
                value={phone}
                onChange={(event) => setPhone(event.target.value)}
                className="w-full rounded-2xl border border-stone-800 bg-stone-900 px-4 py-3 text-sm text-stone-100 outline-none transition focus:border-emerald-500"
                placeholder="+91 98765 43210"
              />
            </label>
          ) : null}

          {mode === "register" ? (
            <label className="block">
              <span className="mb-2 block text-sm font-medium text-stone-300">Region</span>
              <select
                value={regionId}
                onChange={(event) => setRegionId(event.target.value)}
                required
                disabled={regionsLoading}
                className="w-full rounded-2xl border border-stone-800 bg-stone-900 px-4 py-3 text-sm text-stone-100 outline-none transition focus:border-emerald-500 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {regions.map((region) => (
                  <option key={region.id} value={region.id}>
                    {region.region_name} • {region.district}, {region.state}
                  </option>
                ))}
              </select>
            </label>
          ) : null}

          <label className="block">
            <span className="mb-2 block text-sm font-medium text-stone-300">Password</span>
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
              minLength={6}
              className="w-full rounded-2xl border border-stone-800 bg-stone-900 px-4 py-3 text-sm text-stone-100 outline-none transition focus:border-emerald-500"
              placeholder="••••••••"
            />
          </label>

          {error ? (
            <div className="rounded-2xl border border-rose-700/60 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
              {error}
            </div>
          ) : null}

          <button
            type="submit"
            disabled={submitting || (mode === "register" && regionsLoading)}
            className="w-full rounded-2xl bg-emerald-500 px-4 py-3 text-sm font-semibold text-emerald-950 transition hover:bg-emerald-400 disabled:cursor-not-allowed disabled:bg-stone-700 disabled:text-stone-400"
          >
            {submitting
              ? "Please wait..."
              : mode === "login"
                ? "Login"
                : "Register"}
          </button>
        </form>

        <div className="mt-6 text-center text-sm text-stone-400">
          {mode === "login" ? "Need an account?" : "Already registered?"}{" "}
          <button
            type="button"
            onClick={toggleMode}
            className="font-semibold text-emerald-300 transition hover:text-emerald-200"
          >
            {mode === "login" ? "Register here" : "Back to login"}
          </button>
        </div>
      </div>
    </main>
  );
}

export default Login;
