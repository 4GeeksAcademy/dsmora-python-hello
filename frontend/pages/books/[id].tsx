import { useRouter } from 'next/router';
import Link from 'next/link';
import Layout from '@/components/Layout';
import BookDetail from '@/components/BookDetail';
import LoadingSpinner from '@/components/LoadingSpinner';
import ErrorMessage from '@/components/ErrorMessage';
import { useBook } from '@/hooks/useBook';

export default function BookPage() {
  const router = useRouter();
  const { id } = router.query;
  const bookId = id ? parseInt(id as string, 10) : null;
  const { book, isLoading, error, refetch } = useBook(bookId);

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

      {error && <ErrorMessage message={error} onRetry={refetch} />}

      {!isLoading && !error && book && <BookDetail book={book} />}
    </Layout>
  );
}
