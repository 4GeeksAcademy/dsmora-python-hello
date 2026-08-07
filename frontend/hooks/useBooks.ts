import { useState, useEffect, useCallback } from 'react';
import { fetchApi } from '@/lib/api';
import { BookResponse, BookFilters } from '@/types/book';

interface UseBooksResult {
  books: BookResponse[];
  isLoading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useBooks(filters?: BookFilters): UseBooksResult {
  const [books, setBooks] = useState<BookResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const buildQueryString = useCallback((filters?: BookFilters): string => {
    if (!filters) return '';

    const params = new URLSearchParams();
    if (filters.genre) params.append('genre', filters.genre);
    if (filters.status) params.append('status', filters.status);

    const queryString = params.toString();
    return queryString ? `?${queryString}` : '';
  }, []);

  const fetchBooks = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const queryString = buildQueryString(filters);
      const data = await fetchApi<BookResponse[]>(`/books${queryString}`);
      setBooks(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al cargar los libros');
    } finally {
      setIsLoading(false);
    }
  }, [filters, buildQueryString]);

  useEffect(() => {
    fetchBooks();
  }, [fetchBooks]);

  return { books, isLoading, error, refetch: fetchBooks };
}
