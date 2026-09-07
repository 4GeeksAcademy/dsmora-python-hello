/// <reference types="next" />

export interface EventEnvelope {
  event_id: string;
  event: string;
  schema_version: string;
  timestamp: string;
  user_id: string | null;
  anonymous_id: string | null;
  session_id: string;
  context: Record<string, unknown>;
  properties: Record<string, unknown>;
  metadata: {
    source: 'frontend-web';
    environment?: string;
    app_version?: string;
  };
}

export type AllowedFrontendEvent =
  | 'book.viewed'
  | 'book.listed'
  | 'book.reserved'
  | 'book.released'
  | 'user.registered'
  | 'user.logged_in'
  | 'user.login_failed';