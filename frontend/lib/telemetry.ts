/// <reference types="next" />
/**
 * Telemetry helper — API pública: SOLO track(), initTelemetry()
 *
 * Genera y persiste:
 * - session_id en sessionStorage (una vez por sesión de navegador)
 * - anonymous_id en localStorage (una vez por navegador/dispositivo, prefijo anon_ + uuid4)
 *
 * Envía con navigator.sendBeacon (fire-and-forget);
 * fallback a fetch con keepalive: true si sendBeacon no está disponible.
 */

import type { AllowedFrontendEvent, EventEnvelope } from '@/types/telemetry';

const TELEMETRY_ENDPOINT = '/api/telemetry';
const ANONYMOUS_ID_KEY = 'telemetry_anonymous_id';
const CONSENT_KEY = 'telemetry_consent';
const FLUSH_INTERVAL_MS = 60_000; // 60s
const MAX_BATCH_SIZE = 20;
const MAX_RETRIES = 3;

let eventQueue: EventEnvelope[] = [];
let flushTimer: ReturnType<typeof setInterval> | null = null;

// ── Helpers de identidad ──────────────────────────────────────────

function generateUUID(): string {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  // Fallback para navegadores antiguos
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

function getAnonymousId(): string {
  if (typeof window === 'undefined') return '';
  let id = localStorage.getItem(ANONYMOUS_ID_KEY);
  if (!id) {
    id = `anon_${generateUUID()}`;
    localStorage.setItem(ANONYMOUS_ID_KEY, id);
  }
  return id;
}

function getSessionId(): string {
  if (typeof window === 'undefined') return '';
  const key = 'telemetry_session_id';
  let id = sessionStorage.getItem(key);
  if (!id) {
    id = `s_${generateUUID().slice(0, 8)}`;
    sessionStorage.setItem(key, id);
  }
  return id;
}

function hasConsent(): boolean {
  if (typeof window === 'undefined') return false;
  return localStorage.getItem(CONSENT_KEY) === 'true';
}

// ── Whitelist ─────────────────────────────────────────────────────

const ALLOWED_EVENTS: ReadonlySet<string> = new Set([
  'book.viewed',
  'book.listed',
  'book.reserved',
  'book.released',
  'user.registered',
  'user.logged_in',
  'user.login_failed',
]);

function isAllowedEvent(event: string): boolean {
  return ALLOWED_EVENTS.has(event);
}

// ── Sanitization ──────────────────────────────────────────────────

const SENSITIVE_KEYS = new Set(['password', 'token', 'access_token', 'secret', 'hashed_password']);

function sanitize(obj: Record<string, unknown>): Record<string, unknown> {
  const result: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(obj)) {
    if (SENSITIVE_KEYS.has(key.toLowerCase())) continue;
    result[key] = value;
  }
  return result;
}

// ── Track ─────────────────────────────────────────────────────────

export function track(
  event: AllowedFrontendEvent,
  context?: Record<string, unknown>,
  properties?: Record<string, unknown>,
): void {
  if (!hasConsent()) return;
  if (!isAllowedEvent(event)) return;

  const envelope: EventEnvelope = {
    event_id: `evt_${generateUUID()}`,
    event,
    schema_version: '1.0',
    timestamp: new Date().toISOString(),
    user_id: null, // Se llena desde el backend si hay JWT
    anonymous_id: getAnonymousId(),
    session_id: getSessionId(),
    context: sanitize(context ?? {}),
    properties: sanitize(properties ?? {}),
    metadata: {
      source: 'frontend-web',
      environment: process.env.NEXT_PUBLIC_APP_ENV || 'development',
      app_version: process.env.NEXT_PUBLIC_APP_VERSION || '0.1.0',
    },
  };

  eventQueue.push(envelope);

  // Flush inmediato si alcanzamos el batch máximo
  if (eventQueue.length >= MAX_BATCH_SIZE) {
    flush();
  }
}

// ── Flush ─────────────────────────────────────────────────────────

async function flush(): Promise<void> {
  if (eventQueue.length === 0) return;

  const batch = eventQueue.splice(0, MAX_BATCH_SIZE);
  const payload = JSON.stringify({ events: batch });

  // Intentar sendBeacon primero (fire-and-forget)
  if (typeof navigator !== 'undefined' && navigator.sendBeacon) {
    const sent = navigator.sendBeacon(TELEMETRY_ENDPOINT, payload);
    if (sent) return; // Éxito, no necesitamos hacer nada más
  }

  // Fallback: fetch con keepalive
  for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
    try {
      const response = await fetch(TELEMETRY_ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: payload,
        keepalive: true,
      });
      if (response.ok) return;
      // Si es 429 (rate limit), reintentar con backoff
      if (response.status === 429 && attempt < MAX_RETRIES) {
        await new Promise((resolve) => setTimeout(resolve, 1000 * Math.pow(2, attempt)));
        continue;
      }
      return; // Otros errores: descartar el batch
    } catch {
      if (attempt < MAX_RETRIES) {
        await new Promise((resolve) => setTimeout(resolve, 1000 * Math.pow(2, attempt)));
      }
    }
  }
}

// ── Init ──────────────────────────────────────────────────────────

export function initTelemetry(): void {
  if (typeof window === 'undefined') return;

  // Si no hay consentimiento, no inicializar
  if (!hasConsent()) return;

  // Asegurar que anonymous_id y session_id existan
  getAnonymousId();
  getSessionId();

  // Flush automático cada 60s
  if (flushTimer) clearInterval(flushTimer);
  flushTimer = setInterval(flush, FLUSH_INTERVAL_MS);

  // Flush al cerrar página
  window.addEventListener('beforeunload', () => {
    flush();
  });
}

// ── Consentimiento ────────────────────────────────────────────────

export function setConsent(granted: boolean): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(CONSENT_KEY, granted ? 'true' : 'false');
  if (granted) {
    initTelemetry();
  } else {
    if (flushTimer) {
      clearInterval(flushTimer);
      flushTimer = null;
    }
    eventQueue = [];
  }
}

export function getConsent(): boolean {
  return hasConsent();
}