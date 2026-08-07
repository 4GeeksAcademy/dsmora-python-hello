import { FormEvent, useState } from 'react';
import { useRouter } from 'next/router';
import Layout from '@/components/Layout';
import { fetchApi } from '@/lib/api';
import { RegisterRequest, UserRole } from '@/types/auth';

const roles: UserRole[] = ['user', 'manager', 'admin'];

export default function RegisterPage() {
  const router = useRouter();
  const [formData, setFormData] = useState<RegisterRequest>({
    email: '',
    password: '',
    name: '',
    phone: '',
    address: '',
    role: 'user',
  });
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      await fetchApi('/users', {
        method: 'POST',
        body: JSON.stringify(formData),
      });
      router.push('/login');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo crear la cuenta');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Layout>
      <div className="max-w-md mx-auto bg-white rounded-lg shadow-md p-6">
        <h2 className="text-2xl font-semibold text-gray-900 mb-6">Crear cuenta</h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="email"
            placeholder="Email"
            required
            value={formData.email}
            onChange={(event) => setFormData((prev) => ({ ...prev, email: event.target.value }))}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg"
          />

          <input
            type="password"
            placeholder="Password (mínimo 8 caracteres)"
            required
            minLength={8}
            value={formData.password}
            onChange={(event) => setFormData((prev) => ({ ...prev, password: event.target.value }))}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg"
          />

          <input
            type="text"
            placeholder="Nombre"
            required
            value={formData.name}
            onChange={(event) => setFormData((prev) => ({ ...prev, name: event.target.value }))}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg"
          />

          <input
            type="text"
            placeholder="Teléfono"
            required
            value={formData.phone}
            onChange={(event) => setFormData((prev) => ({ ...prev, phone: event.target.value }))}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg"
          />

          <input
            type="text"
            placeholder="Dirección"
            required
            value={formData.address}
            onChange={(event) => setFormData((prev) => ({ ...prev, address: event.target.value }))}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg"
          />

          <div>
            <label htmlFor="role" className="block text-sm font-medium text-gray-700 mb-1">
              Rol
            </label>
            <select
              id="role"
              value={formData.role}
              onChange={(event) =>
                setFormData((prev) => ({ ...prev, role: event.target.value as UserRole }))
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            >
              {roles.map((role) => (
                <option key={role} value={role}>
                  {role}
                </option>
              ))}
            </select>
          </div>

          {error && <p className="text-sm text-red-600">{error}</p>}

          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-blue-600 text-white py-2 rounded-lg font-medium hover:bg-blue-700 disabled:bg-blue-300"
          >
            {isLoading ? 'Creando cuenta...' : 'Registrarse'}
          </button>
        </form>
      </div>
    </Layout>
  );
}
