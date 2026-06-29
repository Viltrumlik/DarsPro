// DarsPro — Zustand auth store
import { create } from "zustand";

import { api, apiError, tokenStore } from "./api";
import type { RegisterResponse, User } from "@/types/api";

interface AuthState {
  user: User | null;
  loading: boolean;
  initialized: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (
    email: string,
    password: string,
    full_name: string
  ) => Promise<void>;
  loadMe: () => Promise<void>;
  loginWithGoogle: (idToken: string) => Promise<void>;
  loginWithTelegram: (payload: Record<string, unknown>) => Promise<void>;
  sendOtp: (phone: string) => Promise<void>;
  verifyOtp: (phone: string, code: string) => Promise<void>;
  updateProfile: (patch: {
    full_name?: string;
    phone?: string | null;
  }) => Promise<void>;
  logout: () => Promise<void>;
}

export const useAuth = create<AuthState>((set) => ({
  user: null,
  loading: false,
  initialized: false,

  async login(email, password) {
    set({ loading: true });
    try {
      const { data } = await api.post("/auth/login", { email, password });
      tokenStore.set(data.access, data.refresh);
      const me = await api.get<User>("/users/me");
      set({ user: me.data });
    } catch (e) {
      throw new Error(apiError(e));
    } finally {
      set({ loading: false });
    }
  },

  async register(email, password, full_name) {
    set({ loading: true });
    try {
      const { data } = await api.post<RegisterResponse>("/auth/register", {
        email,
        password,
        full_name,
      });
      tokenStore.set(data.tokens.access, data.tokens.refresh);
      set({ user: data.user });
    } catch (e) {
      throw new Error(apiError(e));
    } finally {
      set({ loading: false });
    }
  },

  async loginWithGoogle(idToken) {
    set({ loading: true });
    try {
      const { data } = await api.post<RegisterResponse>("/auth/google", {
        id_token: idToken,
      });
      tokenStore.set(data.tokens.access, data.tokens.refresh);
      set({ user: data.user });
    } catch (e) {
      throw new Error(apiError(e));
    } finally {
      set({ loading: false });
    }
  },

  async loginWithTelegram(payload) {
    set({ loading: true });
    try {
      const { data } = await api.post<RegisterResponse>(
        "/auth/telegram",
        payload
      );
      tokenStore.set(data.tokens.access, data.tokens.refresh);
      set({ user: data.user });
    } catch (e) {
      throw new Error(apiError(e));
    } finally {
      set({ loading: false });
    }
  },

  async sendOtp(phone) {
    try {
      await api.post("/auth/otp/send", { phone });
    } catch (e) {
      throw new Error(apiError(e));
    }
  },

  async verifyOtp(phone, code) {
    set({ loading: true });
    try {
      const { data } = await api.post<RegisterResponse>("/auth/otp/verify", {
        phone,
        code,
      });
      tokenStore.set(data.tokens.access, data.tokens.refresh);
      set({ user: data.user });
    } catch (e) {
      throw new Error(apiError(e));
    } finally {
      set({ loading: false });
    }
  },

  async loadMe() {
    if (!tokenStore.access) {
      set({ initialized: true });
      return;
    }
    try {
      const me = await api.get<User>("/users/me");
      set({ user: me.data, initialized: true });
    } catch {
      tokenStore.clear();
      set({ user: null, initialized: true });
    }
  },

  async updateProfile(patch) {
    set({ loading: true });
    try {
      const { data } = await api.patch<User>("/users/me", patch);
      set({ user: data });
    } catch (e) {
      throw new Error(apiError(e));
    } finally {
      set({ loading: false });
    }
  },

  async logout() {
    try {
      if (tokenStore.refresh) {
        await api.post("/auth/logout", { refresh: tokenStore.refresh });
      }
    } catch {
      /* server xatosi muhim emas — baribir tozalaymiz */
    }
    tokenStore.clear();
    set({ user: null });
  },
}));
