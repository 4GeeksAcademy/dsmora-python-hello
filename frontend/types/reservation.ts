import { BookResponse } from '@/types/book';

export type ReservationStatus = 'reserved' | 'cancelled';

export interface ReservedBookResponse {
  id: string;
  user_id: string;
  book_id: number;
  status: ReservationStatus;
  created_at: string;
  book: BookResponse | null;
}
