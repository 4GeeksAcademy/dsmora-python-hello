import { useState, Suspense, lazy } from 'react';
import Head from 'next/head';
import Layout from '@/components/Layout';
import LoadingSpinner from '@/components/LoadingSpinner';
import { useBooks } from '@/hooks/useBooks';
import { BookFilters as BookFiltersType } from '@/types/book';

const BookCard = lazy(() => import('@/components/BookCard'));
const BookFilters = lazy(() => import('@/components/BookFilters'));
const ErrorMessage = lazy(() => import('@/components/ErrorMessage'));
const EmptyState = lazy(() => import('@/components/EmptyState'));

export default function Home() {
  const [filters, setFilters] = useState<BookFiltersType>({});
  const { books, isLoading, error, refetch } = useBooks(filters);

  return (
    <Layout>
      <Head>
        <title>Book Library — Catálogo de Libros</title>
        <meta name="description" content="Explora nuestro catálogo de libros. Encuentra tu próxima lectura favorita en Book Library." />
        <meta name="keywords" content="libros, book library, catálogo, lectura, biblioteca" />
        <meta property="og:title" content="Book Library — Catálogo de Libros" />
        <meta property="og:description" content="Explora nuestro catálogo de libros. Encuentra tu próxima lectura favorita." />
        <meta property="og:type" content="website" />
        <meta property="og:image" content="/image.webp" />
        <meta property="og:image:width" content="1200" />
        <meta property="og:image:height" content="630" />
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content="Book Library — Catálogo de Libros" />
        <meta name="twitter:description" content="Explora nuestro catálogo de libros." />
        <meta name="twitter:image" content="/image.webp" />
      </Head>
      {/* Hero Section with Parallax */}
      <div
        className="hero-parallax relative w-full h-[250px] mb-8"
        style={{ backgroundImage: "url('/image.webp')" }}
      >
        <div className="absolute inset-0 bg-black/40 flex items-center justify-center">
          <h2 className="text-4xl md:text-5xl font-bold text-white text-center drop-shadow-lg">
            Bienvenido a Book Library
          </h2>
        </div>
      </div>

      <h2 className="text-2xl font-semibold text-gray-900 mb-6">
        Catálogo de Libros
      </h2>

      <Suspense fallback={<LoadingSpinner />}>
        <BookFilters filters={filters} onFilterChange={setFilters} />
      </Suspense>

      {isLoading && <LoadingSpinner />}

      {error && (
        <Suspense fallback={null}>
          <ErrorMessage message={error} onRetry={refetch} />
        </Suspense>
      )}

      {!isLoading && !error && books.length === 0 && (
        <Suspense fallback={null}>
          <EmptyState message="No se encontraron libros con los filtros seleccionados" />
        </Suspense>
      )}

      {!isLoading && !error && books.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {books.map((book) => (
            <Suspense key={book.id} fallback={<LoadingSpinner />}>
              <BookCard book={book} onReserved={refetch} />
            </Suspense>
          ))}
        </div>
      )}
    </Layout>
  );
}
