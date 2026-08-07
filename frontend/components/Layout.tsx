import { ReactNode, useEffect, useState } from 'react';
import Link from 'next/link';
import { clearToken, getToken } from '@/lib/auth';
import { ApiError, fetchApi } from '@/lib/api';

interface LayoutProps {
  children: ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const [token, setToken] = useState<string | null>(null);
  const [canManageBooks, setCanManageBooks] = useState(false);

  useEffect(() => {
    const savedToken = getToken();
    setToken(savedToken);

    const resolvePermissions = async () => {
      if (!savedToken) {
        setCanManageBooks(false);
        return;
      }

      const search = new URLSearchParams();
      search.append('allowed_roles', 'admin');
      search.append('allowed_roles', 'manager');

      try {
        await fetchApi(`/auth/authorize?${search.toString()}`, { token: savedToken });
        setCanManageBooks(true);
      } catch (error) {
        if (error instanceof ApiError && error.status === 401) {
          clearToken();
          setToken(null);
        }
        setCanManageBooks(false);
      }
    };

    resolvePermissions();
  }, []);

  const handleLogout = () => {
    clearToken();
    window.location.href = '/';
  };

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between gap-4">
          <Link href="/">
            <h1 className="text-2xl font-bold text-gray-900 cursor-pointer hover:text-blue-600 transition-colors">
              Book Library
            </h1>
          </Link>

          <nav className="flex items-center gap-3 text-sm">
            <Link href="/" className="text-gray-700 hover:text-blue-700">
              Inicio
            </Link>
            {token && (
              <>
                <Link href="/profile" className="text-gray-700 hover:text-blue-700">
                  Perfil
                </Link>
                <Link href="/reservations" className="text-gray-700 hover:text-blue-700">
                  Reservas
                </Link>
              </>
            )}
            {token && canManageBooks && (
              <Link href="/admin/books/new" className="text-gray-700 hover:text-blue-700">
                Crear libro
              </Link>
            )}
            {!token ? (
              <>
                <Link href="/login" className="text-gray-700 hover:text-blue-700">
                  Login
                </Link>
                <Link
                  href="/register"
                  className="bg-blue-600 text-white px-3 py-1.5 rounded-md hover:bg-blue-700"
                >
                  Registro
                </Link>
              </>
            ) : (
              <button
                onClick={handleLogout}
                className="bg-gray-900 text-white px-3 py-1.5 rounded-md hover:bg-gray-700"
              >
                Salir
              </button>
            )}
          </nav>
        </div>
      </header>

      <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full">
        {children}
      </main>

      <footer className="bg-white border-t border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <p className="text-center text-gray-500 text-sm">
            © 2026 Book Library. Built with Next.js & Tailwind CSS.
          </p>
        </div>
      </footer>
    </div>
  );
}
