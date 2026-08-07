import { useState } from 'react';
import Layout from '@/components/Layout';
import BookCard from '@/components/BookCard';
import BookFilters from '@/components/BookFilters';
import LoadingSpinner from '@/components/LoadingSpinner';
import ErrorMessage from '@/components/ErrorMessage';
import EmptyState from '@/components/EmptyState';
import { useBooks } from '@/hooks/useBooks';
import { BookFilters as BookFiltersType } from '@/types/book';

export default function Home() {
  const [filters, setFilters] = useState<BookFiltersType>({});
  const { books, isLoading, error, refetch } = useBooks(filters);

  return (
    <Layout>
      <h2 className="text-2xl font-semibold text-gray-900 mb-6">
        Catálogo de Libros
      </h2>

      <BookFilters filters={filters} onFilterChange={setFilters} />

      {isLoading && <LoadingSpinner />}

      {error && <ErrorMessage message={error} onRetry={refetch} />}

      {!isLoading && !error && books.length === 0 && (
        <EmptyState message="No se encontraron libros con los filtros seleccionados" />
      )}

      {!isLoading && !error && books.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {books.map((book) => (
            <BookCard key={book.id} book={book} />
          ))}
        </div>
      )}
    </Layout>
  );
}
