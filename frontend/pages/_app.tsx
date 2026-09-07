import { useEffect } from 'react';
import "@/styles/globals.css";
import type { AppProps } from "next/app";
import { initTelemetry } from "@/lib/telemetry";

export default function App({ Component, pageProps }: AppProps) {
  useEffect(() => {
    initTelemetry();
  }, []);

  return <Component {...pageProps} />;
}
