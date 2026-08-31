import { useEffect, useState, Suspense, lazy } from 'react';
import Layout from '@/components/Layout';
import LoadingSpinner from '@/components/LoadingSpinner';
import { useAuthGuard } from '@/hooks/useAuthGuard';
import { clearToken } from '@/lib/auth';
import { ApiError, fetchApi } from '@/lib/api';
import { AuthMeResponse } from '@/types/auth';
import { ReservedBookResponse } from '@/types/reservation';
import { useRouter } from 'next/router';

const ErrorMessage = lazy(() => import('@/components/ErrorMessage'));

export default function ProfilePage() {
  const router = useRouter();
  const { isChecking, token } = useAuthGuard();
  const [data, setData] = useState<AuthMeResponse | null>(null);
  const [reservations, setReservations] = useState<ReservedBookResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isChecking || !token) return;

    const loadProfile = async () => {
      setError(null);
      setIsLoading(true);
      try {
        const [profile, reservedBooks] = await Promise.all([
          fetchApi<AuthMeResponse>('/auth/me', { token }),
          fetchApi<ReservedBookResponse[]>('/books/reserved', { token }),
        ]);
        setData(profile);
        setReservations(reservedBooks);
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
        setError(err instanceof Error ? err.message : 'No se pudo cargar el perfil');
      } finally {
        setIsLoading(false);
      }
    };

    loadProfile();
  }, [isChecking, token, router]);

  if (isChecking || isLoading) {
    return (
      <Layout>
        <LoadingSpinner />
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout>
        <Suspense fallback={null}>
          <ErrorMessage message={error} />
        </Suspense>
      </Layout>
    );
  }

  if (!data) {
    return null;
  }

  return (
    <Layout>
      <div className="max-w-2xl mx-auto bg-white rounded-lg shadow-md p-6 space-y-4">
        <h2 className="text-2xl font-semibold text-gray-900">Mi perfil</h2>

        <div>
          <p className="text-sm text-gray-500">Email</p>
          <p className="text-lg text-gray-900">{data.email}</p>
        </div>

        <div>
          <p className="text-sm text-gray-500">Rol</p>
          <p className="text-lg text-gray-900">{data.role}</p>
        </div>

        <div>
          <p className="text-sm text-gray-500">Nombre</p>
          <p className="text-lg text-gray-900">{data.profile.name}</p>
        </div>

        <div>
          <p className="text-sm text-gray-500">Teléfono</p>
          <p className="text-lg text-gray-900">{data.profile.phone}</p>
        </div>

        <div>
          <p className="text-sm text-gray-500">Dirección</p>
          <p className="text-lg text-gray-900">{data.profile.address}</p>
        </div>

        <div className="border-t border-gray-200 pt-4">
          <h3 className="text-lg font-semibold text-gray-900">Libros reservados</h3>
          {reservations.length === 0 ? (
            <p className="mt-2 text-gray-600">No tienes libros reservados.</p>
          ) : (
            <ul className="mt-3 space-y-2">
              {reservations.map((reservation) => (
                <li key={reservation.id} className="text-gray-700">
                  {reservation.book?.title || `Libro #${reservation.book_id}`}
                  {reservation.book && `, ${reservation.book.author}`}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </Layout>
  );
}
