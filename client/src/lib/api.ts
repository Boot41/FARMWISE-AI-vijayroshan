import axios, {
  AxiosError,
  type AxiosResponse,
  type InternalAxiosRequestConfig,
} from "axios";
import {
  clearTokens,
  getAccessToken,
  getRefreshToken,
  setTokens,
} from "./auth";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8010";

export interface ApiResponse<T> {
  success: boolean;
  message: string;
  data: T;
}

export interface ApiErrorResponse {
  success: false;
  message: string;
  data: null;
}

export interface Region {
  id: string;
  state: string;
  district: string;
  region_name: string;
  dominant_soil_type: string;
  default_water_availability: string;
  climate_zone: string;
  created_at: string;
}

export interface WeatherForecast {
  id: string;
  region_id: string;
  forecast_date: string;
  min_temp: number;
  max_temp: number;
  expected_rainfall_mm: number;
  humidity_pct: number;
  wind_speed_kmph: number;
  forecast_generated_at: string;
  created_at: string;
}

export interface MandiPrice {
  id: string;
  region_id: string;
  crop_name: string;
  price_per_quintal: number;
  recorded_date: string;
  created_at: string;
}

export interface RegionCrop {
  id: string;
  region_id: string;
  crop_name: string;
  crop_season: string;
  suitability_score: number;
  notes: string | null;
  created_at: string;
}

export interface UserProfile {
  id: string;
  name: string;
  email: string;
  phone_number: string | null;
  region_id: string;
  water_availability: string | null;
  irrigation_type: string | null;
  current_crop: string | null;
  created_at: string;
  updated_at: string;
  region: Region;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface AuthPayload {
  tokens: TokenPair;
  user: UserProfile;
}

export interface AccessTokenPayload {
  access_token: string;
  token_type: string;
}

export interface ChatMessageMetadata {
  structured?: boolean;
  intent?: string;
  data?: Record<string, unknown>;
  source?: string;
  [key: string]: unknown;
}

export interface ChatMessage {
  id: string;
  session_id: string;
  role: "user" | "assistant" | string;
  message_text: string;
  message_metadata: ChatMessageMetadata | null;
  created_at: string;
}

export interface ChatSessionSummary {
  id: string;
  user_id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
}

export interface ChatSessionDetail extends ChatSessionSummary {
  messages: ChatMessage[];
}

export interface ChatReply {
  session_id: string;
  session_title: string | null;
  reply: string;
}

export interface CropAdvisoryCardData {
  crop?: string;
  season?: string;
  sowing_window?: string;
  harvest_window?: string;
  water_requirement?: string;
  estimated_cost?: number | string;
  expected_yield?: number | string;
  expected_revenue?: number | string;
  notes?: string;
}

export interface PestDiagnosisCardData {
  pest_name?: string;
  crop?: string;
  symptoms?: string;
  treatment?: string;
  dosage?: string;
  frequency?: string;
  organic_alternative?: string;
  warning?: string;
}

export interface MarketTimingCardData {
  crop?: string;
  current_price?: number | string;
  price_unit?: string;
  trend?: string;
  trend_pct?: number | string;
  advice?: string;
}

export interface IrrigationCardData {
  next_watering_date?: string;
  skip_dates?: string[] | string;
  expected_rainfall_mm?: number | string;
  rainfall_date?: string;
  reason?: string;
}

interface RetryableRequestConfig extends InternalAxiosRequestConfig {
  _retry?: boolean;
}

const api = axios.create({
  baseURL: API_BASE_URL,
});

let refreshPromise: Promise<string> | null = null;

function redirectToLogin() {
  if (window.location.pathname !== "/login") {
    window.location.assign("/login");
  }
}

function extractEnvelopeMessage(payload: unknown): string | null {
  if (
    payload &&
    typeof payload === "object" &&
    "message" in payload &&
    typeof payload.message === "string"
  ) {
    return payload.message;
  }

  return null;
}

async function refreshAccessToken(): Promise<string> {
  if (!refreshPromise) {
    const currentRefreshToken = getRefreshToken();

    if (!currentRefreshToken) {
      clearTokens();
      redirectToLogin();
      throw new Error("Session expired");
    }

    refreshPromise = axios
      .post<ApiResponse<AccessTokenPayload>>(
        `${API_BASE_URL}/api/auth/refresh`,
        {
          refresh_token: currentRefreshToken,
        },
      )
      .then((response) => {
        const nextAccessToken = response.data.data.access_token;
        setTokens(nextAccessToken, currentRefreshToken);
        return nextAccessToken;
      })
      .catch((error: unknown) => {
        clearTokens();
        redirectToLogin();
        throw error;
      })
      .finally(() => {
        refreshPromise = null;
      });
  }

  return refreshPromise;
}

api.interceptors.request.use((config) => {
  const token = getAccessToken();

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiErrorResponse>) => {
    const originalRequest = error.config as RetryableRequestConfig | undefined;

    if (
      error.response?.status === 401 &&
      originalRequest &&
      !originalRequest._retry &&
      getRefreshToken()
    ) {
      originalRequest._retry = true;

      try {
        const nextAccessToken = await refreshAccessToken();
        originalRequest.headers.Authorization = `Bearer ${nextAccessToken}`;
        return api(originalRequest);
      } catch (refreshError) {
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  },
);

function unwrap<T>(promise: Promise<AxiosResponse<ApiResponse<T>>>): Promise<T> {
  return promise.then((response) => response.data.data);
}

export function getApiErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    return (
      extractEnvelopeMessage(error.response?.data) ||
      error.response?.statusText ||
      error.message ||
      "Something went wrong"
    );
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Something went wrong";
}

export async function login(email: string, password: string): Promise<AuthPayload> {
  return unwrap(api.post("/api/auth/login", { email, password }));
}

export async function register(
  name: string,
  email: string,
  password: string,
  phone: string | null,
  region_id: string,
): Promise<AuthPayload> {
  return unwrap(
    api.post("/api/auth/register", {
      name,
      email,
      password,
      phone_number: phone,
      region_id,
    }),
  );
}

export async function logout(): Promise<void> {
  const currentRefreshToken = getRefreshToken();

  try {
    if (currentRefreshToken) {
      await api.post("/api/auth/logout", {
        refresh_token: currentRefreshToken,
      });
    }
  } finally {
    clearTokens();
  }
}

export async function getMe(): Promise<UserProfile> {
  return unwrap(api.get("/api/users/me"));
}

export async function getRegions(): Promise<Region[]> {
  return unwrap(api.get("/api/data/regions"));
}

export async function getWeather(region_id: string): Promise<WeatherForecast[]> {
  return unwrap(api.get(`/api/data/regions/${region_id}/weather`));
}

export async function getPrices(region_id: string): Promise<MandiPrice[]> {
  return unwrap(api.get(`/api/data/regions/${region_id}/prices`));
}

export async function getRegionCrops(region_id: string): Promise<RegionCrop[]> {
  return unwrap(api.get(`/api/data/regions/${region_id}/crops`));
}

export async function sendMessage(
  session_id: string | null,
  message: string,
): Promise<ChatReply> {
  return unwrap(
    api.post("/api/chat/message", {
      session_id,
      message,
    }),
  );
}

export async function getSessions(): Promise<ChatSessionSummary[]> {
  return unwrap(api.get("/api/chat/sessions"));
}

export async function getSessionMessages(
  session_id: string,
): Promise<ChatSessionDetail> {
  return unwrap(api.get(`/api/chat/sessions/${session_id}`));
}

export default api;
