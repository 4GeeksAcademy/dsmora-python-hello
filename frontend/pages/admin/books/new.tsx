import { FormEvent, useState } from 'react';
import { useRouter } from 'next/router';
import Layout from '@/components/Layout';
import LoadingSpinner from '@/components/LoadingSpinner';
import { useAuthGuard } from '@/hooks/useAuthGuard';
import { clearToken } from '@/lib/auth';
import { ApiError, fetchApi } from '@/lib/api';
import { BookGenre, BookStatus } from '@/types/book';

const genres: BookGenre[] = ['fiction', 'non-fiction', 'mystery', 'sci-fi'];
const statuses: BookStatus[] = ['available', 'checked_out'];

export default function CreateBookPage() {
  const router = useRouter();
  const { isChecking, token } = useAuthGuard({ roles: ['admin', 'manager'] });
  const [formData, setFormData] = useState({
    title: '',
    author: '',
    genre: 'fiction' as BookGenre,
    pages: 1,
    status: 'available' as BookStatus,
  });
  const [error, setError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!token) return;

    setError(null);
    setIsSaving(true);

    try {
      await fetchApi('/books', {
        method: 'POST',
        token,
        body: JSON.stringify(formData),
      });
      router.push('/');
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
      setError(err instanceof Error ? err.message : 'No se pudo crear el libro');
    } finally {
      setIsSaving(false);
    }
  };

  if (isChecking) {
    return (
      <Layout>
        <LoadingSpinner />
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="max-w-xl mx-auto bg-white rounded-lg shadow-md p-6">
        <h2 className="text-2xl font-semibold text-gray-900 mb-6">Crear libro</h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="text"
            required
            placeholder="Título"
            value={formData.title}
            onChange={(event) => setFormData((prev) => ({ ...prev, title: event.target.value }))}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg"
          />

          <input
            type="text"
            required
            placeholder="Autor"
            value={formData.author}
            onChange={(event) => setFormData((prev) => ({ ...prev, author: event.target.value }))}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg"
          />

          <select
            value={formData.genre}
            onChange={(event) =>
              setFormData((prev) => ({ ...prev, genre: event.target.value as BookGenre }))
            }
            className="w-full px-3 py-2 border border-gray-300 rounded-lg"
          >
            {genres.map((genre) => (
              <option key={genre} value={genre}>
                {genre}
              </option>
            ))}
          </select>

          <input
            type="number"
            min={1}
            required
            value={formData.pages}
            onChange={(event) => setFormData((prev) => ({ ...prev, pages: Number(event.target.value) }))}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg"
          />

          <select
            value={formData.status}
            onChange={(event) =>
              setFormData((prev) => ({ ...prev, status: event.target.value as BookStatus }))
            }
            className="w-full px-3 py-2 border border-gray-300 rounded-lg"
          >
            {statuses.map((status) => (
              <option key={status} value={status}>
                {status}
              </option>
            ))}
          </select>

          {error && <p className="text-sm text-red-600">{error}</p>}

          <button
            type="submit"
            disabled={isSaving}
            className="w-full bg-blue-600 text-white py-2 rounded-lg font-medium hover:bg-blue-700 disabled:bg-blue-300"
          >
            {isSaving ? 'Guardando...' : 'Crear libro'}
          </button>
        </form>
      </div>
    </Layout>
  );
}
