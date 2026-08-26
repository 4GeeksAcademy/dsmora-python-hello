import { memo } from 'react';

function LoadingSpinner() {
  'use cache';
  return (
    <div className="flex justify-center items-center py-12">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>
  );
}

export default memo(LoadingSpinner);
