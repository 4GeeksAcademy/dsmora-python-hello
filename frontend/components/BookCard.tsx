import Link from 'next/link';
import { memo } from 'react';
import { BookResponse } from '@/types/book';

interface BookCardProps {
  book: BookResponse;
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

function BookCard({ book }: BookCardProps) {
  return (
    <Link href={`/books/${book.id}`}>
      <div className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow duration-200 p-4 cursor-pointer h-full">
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
      </div>
    </Link>
  );
}

export default memo(BookCard);
