import { BookFilters as BookFiltersType, BookGenre, BookStatus } from '@/types/book';

interface BookFiltersProps {
  filters: BookFiltersType;
  onFilterChange: (filters: BookFiltersType) => void;
}

const genres: BookGenre[] = ['fiction', 'non-fiction', 'mystery', 'sci-fi'];
const statuses: BookStatus[] = ['available', 'checked_out'];

export default function BookFilters({ filters, onFilterChange }: BookFiltersProps) {
  const handleGenreChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value as BookGenre | '';
    onFilterChange({
      ...filters,
      genre: value || undefined,
    });
  };

  const handleStatusChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value as BookStatus | '';
    onFilterChange({
      ...filters,
      status: value || undefined,
    });
  };

  const handleClearFilters = () => {
    onFilterChange({});
  };

  const hasActiveFilters = filters.genre || filters.status;

  return (
    <div className="bg-white rounded-lg shadow-md p-4 mb-6">
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-end">
        <div className="w-full sm:w-auto">
          <label htmlFor="genre" className="block text-sm font-medium text-gray-700 mb-1">
            Género
          </label>
          <select
            id="genre"
            value={filters.genre || ''}
            onChange={handleGenreChange}
            className="w-full sm:w-48 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Todos</option>
            {genres.map((genre) => (
              <option key={genre} value={genre}>
                {genre}
              </option>
            ))}
          </select>
        </div>

        <div className="w-full sm:w-auto">
          <label htmlFor="status" className="block text-sm font-medium text-gray-700 mb-1">
            Estado
          </label>
          <select
            id="status"
            value={filters.status || ''}
            onChange={handleStatusChange}
            className="w-full sm:w-48 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Todos</option>
            {statuses.map((status) => (
              <option key={status} value={status}>
                {status === 'available' ? 'Disponible' : 'Prestado'}
              </option>
            ))}
          </select>
        </div>

        {hasActiveFilters && (
          <button
            onClick={handleClearFilters}
            className="px-4 py-2 text-gray-600 hover:text-gray-800 font-medium transition-colors"
          >
            Limpiar filtros
          </button>
        )}
      </div>
    </div>
  );
}
