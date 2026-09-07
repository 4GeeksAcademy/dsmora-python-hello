"""
Script para crear la tabla telemetry_events en Supabase.

Usa la REST API de Supabase (Management API) o direct SQL via el endpoint /rest/v1/.
Como alternativa, genera el SQL para ejecutar manualmente en el SQL Editor de Supabase.
"""
import os
import sys
from pathlib import Path

import httpx

# Cargar .env manualmente si no está cargado
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

SQL_STATEMENT = """
-- Crear tabla telemetry_events
CREATE TABLE IF NOT EXISTS telemetry_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ NOT NULL,
    service TEXT NOT NULL,
    event_type TEXT NOT NULL,
    level TEXT DEFAULT 'info',
    value NUMERIC NULL,
    message TEXT NULL,
    tags JSONB DEFAULT '{}'::jsonb
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_telemetry_events_timestamp ON telemetry_events (timestamp);
CREATE INDEX IF NOT EXISTS idx_telemetry_events_event_type ON telemetry_events (event_type);
CREATE INDEX IF NOT EXISTS idx_telemetry_events_tags ON telemetry_events USING GIN (tags);

-- Revocar UPDATE/DELETE explícitamente (los eventos son inmutables)
REVOKE UPDATE, DELETE ON telemetry_events FROM anon, authenticated, service_role;
"""


def create_table_via_sql():
    """Intenta ejecutar SQL directo en Supabase via su API de gestión."""
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        print("ERROR: SUPABASE_URL o SUPABASE_SERVICE_ROLE_KEY no están configuradas en .env")
        print("\n--- SQL para ejecutar manualmente en Supabase SQL Editor ---")
        print(SQL_STATEMENT)
        return False

    project_ref = SUPABASE_URL.replace("https://", "").split(".")[0]
    management_url = f"https://api.supabase.com/v1/projects/{project_ref}/sql"

    headers = {
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
    }

    payload = {"query": SQL_STATEMENT}

    try:
        response = httpx.post(management_url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200 or response.status_code == 201:
            print("✅ Tabla 'telemetry_events' creada exitosamente en Supabase.")
            return True
        else:
            print(f"⚠️  Error al crear tabla vía Management API: {response.status_code}")
            print(f"Respuesta: {response.text[:500]}")
            print("\n--- SQL alternativo para ejecutar manualmente ---")
            print(SQL_STATEMENT)
            return False
    except Exception as e:
        print(f"⚠️  Error de conexión: {e}")
        print("\n--- SQL para ejecutar manualmente en Supabase SQL Editor ---")
        print(SQL_STATEMENT)
        return False


if __name__ == "__main__":
    print("=== Crear tabla telemetry_events en Supabase ===\n")
    success = create_table_via_sql()
    if not success:
        sys.exit(1)
    sys.exit(0)