import Link from 'next/link';
import { memo, useState } from 'react';
import { useRouter } from 'next/router';
import { clearToken, getToken } from '@/lib/auth';
import { ApiError, fetchApi } from '@/lib/api';
import { BookResponse } from '@/types/book';

interface BookCardProps {
  book: BookResponse;
  onReserved: () => void;
}

const genreColors: Record<string, string> = {
  'fiction': 'bg-blue-100 text-blue-800',
  'non-fiction': 'bg-green-100 text-green-800',
  'mystery': 'bg-purple-100 text-purple-800',
  'sci-fi': 'bg-orange-100 text-orange-800',
};

const statusColors: Record<string, string> = {
  'available': 'bg-green-100 text-green-800',
  'checked_out': 'bg-orange-100 text-orange-800',
};

const statusLabels: Record<string, string> = {
  'available': 'Disponible',
  'checked_out': 'Prestado',
};

function BookCard({ book, onReserved }: BookCardProps) {
  'use cache';
  const router = useRouter();
  const [isReserving, setIsReserving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleReserve = async () => {
    const token = getToken();
    if (!token) {
      router.push('/login');
      return;
    }

    setError(null);
    setIsReserving(true);
    try {
      await fetchApi(`/books/${book.id}/reserve`, { method: 'POST', token });
      onReserved();
      router.push('/reservations');
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        clearToken();
        router.push('/login');
        return;
      }
      setError(err instanceof Error ? err.message : 'No se pudo reservar el libro');
    } finally {
      setIsReserving(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow duration-200 p-4 h-full">
      <Link href={`/books/${book.id}`} className="block">
        <h3 className="text-lg font-semibold text-gray-900 mb-2 line-clamp-2">
          {book.title}
        </h3>
        <p className="text-gray-600 mb-3">{book.author}</p>

        <div className="flex flex-wrap gap-2 mb-3">
          <span
            className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${genreColors[book.genre] || 'bg-gray-100 text-gray-800'}`}
          >
            {book.genre}
          </span>
          <span
            className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${statusColors[book.status] || 'bg-gray-100 text-gray-800'}`}
          >
            {statusLabels[book.status] || book.status}
          </span>
        </div>

        <p className="text-sm text-gray-500">{book.pages} páginas</p>
      </Link>
      {book.status === 'available' && (
        <div className="mt-4">
          <button
            type="button"
            onClick={handleReserve}
            disabled={isReserving}
            className="w-full bg-blue-600 text-white px-3 py-2 rounded-lg font-medium hover:bg-blue-700 disabled:bg-blue-300"
          >
            {isReserving ? 'Reservando...' : 'Reservar'}
          </button>
          {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
        </div>
      )}
    </div>
  );
}

export default memo(BookCard);
