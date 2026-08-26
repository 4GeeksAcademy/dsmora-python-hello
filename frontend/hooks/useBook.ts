import { useState, useEffect, useCallback } from 'react';
import { fetchApi } from '@/lib/api';
import { BookResponse } from '@/types/book';
'use cache';

interface UseBookResult {
  book: BookResponse | null;
  isLoading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useBook(id: number | null): UseBookResult {
  const [book, setBook] = useState<BookResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchBook = useCallback(async () => {
    if (id === null) {
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const data = await fetchApi<BookResponse>(`/books/${id}`);
      setBook(data);
    } catch (err) {
      if (err instanceof Error && err.message.includes('404')) {
        setError('Libro no encontrado');
      } else {
        setError(err instanceof Error ? err.message : 'Error al cargar el libro');
      }
    } finally {
      setIsLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchBook();
  }, [fetchBook]);

  return { book, isLoading, error, refetch: fetchBook };
}
