const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://silver-guide-7vgxwxwq9pjg2x49x-8000.app.github.dev';

export async function fetchApi<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const url = `${BASE_URL}${path}`;

  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    const message = errorData?.detail || `HTTP error! status: ${response.status}`;
    throw new Error(message);
  }

  return response.json();
}
