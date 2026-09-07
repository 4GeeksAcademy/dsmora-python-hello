import { useState, useEffect, Suspense, lazy } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import Layout from '@/components/Layout';
import LoadingSpinner from '@/components/LoadingSpinner';
import { useBook } from '@/hooks/useBook';
import { clearToken, getToken } from '@/lib/auth';
import { ApiError, fetchApi } from '@/lib/api';
import { track } from '@/lib/telemetry';

const BookDetail = lazy(() => import('@/components/BookDetail'));
const ErrorMessage = lazy(() => import('@/components/ErrorMessage'));

export default function BookPage() {
  const router = useRouter();
  const { id } = router.query;
  const bookId = id ? parseInt(id as string, 10) : null;
  const { book, isLoading, error, refetch } = useBook(bookId);
  const [actionError, setActionError] = useState<string | null>(null);
  const [isReserving, setIsReserving] = useState(false);

  // Telemetry: book.viewed
  useEffect(() => {
    if (book) {
      track('book.viewed', { book_id: book.id, genre: book.genre, title: book.title });
    }
  }, [book]);

  const handleReserve = async () => {
    if (!bookId) return;

    const token = getToken();
    if (!token) {
      clearToken();
      router.push('/login');
      return;
    }

    setActionError(null);
    setIsReserving(true);

    try {
      await fetchApi(`/books/${bookId}/reserve`, {
        method: 'POST',
        token,
      });
      track('book.reserved', { book_id: bookId, title: book?.title });
      refetch();
      router.push('/reservations');
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        clearToken();
        router.push('/login');
        return;
      }
      if (err instanceof ApiError && err.status === 403) {
        router.push('/');
        return;
      }
      setActionError(err instanceof Error ? err.message : 'No se pudo reservar el libro');
    } finally {
      setIsReserving(false);
    }
  };

  return (
    <Layout>
      <div className="mb-6">
        <Link
          href="/"
          className="text-blue-600 hover:text-blue-800 font-medium inline-flex items-center"
        >
          <svg
            className="w-5 h-5 mr-2"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M10 19l-7-7m0 0l7-7m-7 7h18"
            />
          </svg>
          Volver al listado
        </Link>
      </div>

      {isLoading && <LoadingSpinner />}

      {error && (
        <Suspense fallback={null}>
          <ErrorMessage message={error} onRetry={refetch} />
        </Suspense>
      )}

      {!isLoading && !error && book && (
        <div className="space-y-4">
          <Suspense fallback={<LoadingSpinner />}>
            <BookDetail book={book} />
          </Suspense>

          {book.status === 'available' && (
            <div className="max-w-2xl mx-auto flex flex-col items-start gap-3">
              <button
                onClick={handleReserve}
                disabled={isReserving}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-700 disabled:bg-blue-300"
              >
                {isReserving ? 'Reservando...' : 'Reservar libro'}
              </button>
              {actionError && <p className="text-sm text-red-600">{actionError}</p>}
            </div>
          )}
        </div>
      )}
    </Layout>
  );
}
