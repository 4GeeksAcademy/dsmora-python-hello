import { ProfileResponse } from '@/types/profile';

export type UserRole = 'user' | 'manager' | 'admin';

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  name: string;
  phone: string;
  address: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface AuthMeResponse {
  email: string;
  role: UserRole;
  profile: ProfileResponse;
}
