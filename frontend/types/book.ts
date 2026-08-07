export type BookGenre = 'fiction' | 'non-fiction' | 'mystery' | 'sci-fi';
export type BookStatus = 'available' | 'checked_out';

export interface BookResponse {
  id: number;
  title: string;
  author: string;
  genre: BookGenre;
  pages: number;
  status: BookStatus;
}

export interface BookFilters {
  genre?: BookGenre;
  status?: BookStatus;
}
