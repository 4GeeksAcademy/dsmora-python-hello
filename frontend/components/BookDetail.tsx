import { memo } from 'react';
import { BookResponse } from '@/types/book';

interface BookDetailProps {
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

function BookDetail({ book }: BookDetailProps) {
  'use cache';
  return (
    <div className="bg-white rounded-lg shadow-md p-6 max-w-2xl mx-auto">
      <h1 className="text-3xl font-bold text-gray-900 mb-4">{book.title}</h1>

      <div className="space-y-4">
        <div>
          <h2 className="text-sm font-medium text-gray-500 uppercase tracking-wide">Autor</h2>
          <p className="text-lg text-gray-900">{book.author}</p>
        </div>

        <div>
          <h2 className="text-sm font-medium text-gray-500 uppercase tracking-wide">Género</h2>
          <span
            className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${genreColors[book.genre] || 'bg-gray-100 text-gray-800'}`}
          >
            {book.genre}
          </span>
        </div>

        <div>
          <h2 className="text-sm font-medium text-gray-500 uppercase tracking-wide">Estado</h2>
          <span
            className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${statusColors[book.status] || 'bg-gray-100 text-gray-800'}`}
          >
            {statusLabels[book.status] || book.status}
          </span>
        </div>

        <div>
          <h2 className="text-sm font-medium text-gray-500 uppercase tracking-wide">Páginas</h2>
          <p className="text-lg text-gray-900">{book.pages}</p>
        </div>
      </div>
    </div>
  );
}

export default memo(BookDetail);
