const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://silver-guide-7vgxwxwq9pjg2x49x-8000.app.github.dev';

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

interface FetchApiOptions extends RequestInit {
  token?: string;
}

export async function fetchApi<T>(
  path: string,
  options?: FetchApiOptions
): Promise<T> {
  const url = `${BASE_URL}${path}`;
  const headers = new Headers(options?.headers);
  headers.set('Content-Type', 'application/json');

  if (options?.token) {
    headers.set('Authorization', `Bearer ${options.token}`);
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    const message = errorData?.detail || `HTTP error! status: ${response.status}`;
    throw new ApiError(message, response.status);
  }

  if (response.status === 204) {
    return null as T;
  }

  return response.json();
}
