import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import { clearToken, getToken } from '@/lib/auth';
import { ApiError, fetchApi } from '@/lib/api';
import { UserRole } from '@/types/auth';

interface UseAuthGuardOptions {
  roles?: UserRole[];
}

interface UseAuthGuardResult {
  isChecking: boolean;
  token: string | null;
}

export function useAuthGuard(options?: UseAuthGuardOptions): UseAuthGuardResult {
  const router = useRouter();
  const [isChecking, setIsChecking] = useState(true);
  const [token, setToken] = useState<string | null>(null);
  const rolesKey = options?.roles?.join(',') || '';

  useEffect(() => {
    const validateSession = async () => {
      const savedToken = getToken();

      if (!savedToken) {
        clearToken();
        router.replace('/login');
        return;
      }

      try {
        if (options?.roles && options.roles.length > 0) {
          const search = new URLSearchParams();
          for (const role of options.roles) {
            search.append('allowed_roles', role);
          }
          await fetchApi(`/auth/authorize?${search.toString()}`, { token: savedToken });
        } else {
          await fetchApi('/auth/me', { token: savedToken });
        }

        setToken(savedToken);
        setIsChecking(false);
      } catch (error) {
        if (error instanceof ApiError && error.status === 401) {
          clearToken();
          router.replace('/login');
          return;
        }
        if (error instanceof ApiError && error.status === 403) {
          router.replace('/');
          return;
        }

        clearToken();
        router.replace('/login');
      }
    };

    validateSession();
  }, [router, rolesKey]);

  return { isChecking, token };
}
