import { useEffect, useState, Suspense, lazy } from 'react';
import { useRouter } from 'next/router';
import Layout from '@/components/Layout';
import LoadingSpinner from '@/components/LoadingSpinner';
import { useAuthGuard } from '@/hooks/useAuthGuard';
import { clearToken } from '@/lib/auth';
import { ApiError, fetchApi } from '@/lib/api';
import { ReservedBookResponse } from '@/types/reservation';

const ErrorMessage = lazy(() => import('@/components/ErrorMessage'));
const EmptyState = lazy(() => import('@/components/EmptyState'));

export default function ReservationsPage() {
  const router = useRouter();
  const { isChecking, token } = useAuthGuard();
  const [reservations, setReservations] = useState<ReservedBookResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isChecking || !token) return;

    const loadReservations = async () => {
      setError(null);
      setIsLoading(true);
      try {
        const response = await fetchApi<ReservedBookResponse[]>('/books/reserved', { token });
        setReservations(response);
      } catch (err) {
        if (err instanceof ApiError && err.status === 401) {
          clearToken();
          router.replace('/login');
          return;
        }
        if (err instanceof ApiError && err.status === 403) {
          router.replace('/');
          return;
        }
        setError(err instanceof Error ? err.message : 'No se pudieron cargar las reservas');
      } finally {
        setIsLoading(false);
      }
    };

    loadReservations();
  }, [isChecking, token, router]);

  return (
    <Layout>
      <h2 className="text-2xl font-semibold text-gray-900 mb-6">Mis reservas</h2>

      {(isChecking || isLoading) && <LoadingSpinner />}
      {error && (
        <Suspense fallback={null}>
          <ErrorMessage message={error} />
        </Suspense>
      )}

      {!isChecking && !isLoading && !error && reservations.length === 0 && (
        <Suspense fallback={null}>
          <EmptyState message="No tienes reservas activas" />
        </Suspense>
      )}

      {!isChecking && !isLoading && !error && reservations.length > 0 && (
        <div className="space-y-4">
          {reservations.map((reservation) => (
            <div key={reservation.id} className="bg-white rounded-lg shadow-md p-4">
              <p className="font-semibold text-gray-900">
                {reservation.book?.title || `Libro #${reservation.book_id}`}
              </p>
              <p className="text-gray-600">Estado: {reservation.status}</p>
              <p className="text-gray-500 text-sm">
                Fecha: {new Date(reservation.created_at).toLocaleString()}
              </p>
            </div>
          ))}
        </div>
      )}
    </Layout>
  );
}
