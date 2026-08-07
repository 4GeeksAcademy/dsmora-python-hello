import { useEffect, useState } from 'react';
import Layout from '@/components/Layout';
import LoadingSpinner from '@/components/LoadingSpinner';
import ErrorMessage from '@/components/ErrorMessage';
import { useAuthGuard } from '@/hooks/useAuthGuard';
import { clearToken } from '@/lib/auth';
import { ApiError, fetchApi } from '@/lib/api';
import { AuthMeResponse } from '@/types/auth';
import { useRouter } from 'next/router';

export default function ProfilePage() {
  const router = useRouter();
  const { isChecking, token } = useAuthGuard();
  const [data, setData] = useState<AuthMeResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isChecking || !token) return;

    const loadProfile = async () => {
      setError(null);
      setIsLoading(true);
      try {
        const response = await fetchApi<AuthMeResponse>('/auth/me', { token });
        setData(response);
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
        <ErrorMessage message={error} />
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
      </div>
    </Layout>
  );
}
