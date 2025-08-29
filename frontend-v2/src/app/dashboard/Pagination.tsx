'use client';

import { Button } from "@/components/ui/button";

interface PaginationProps {
  total: number;
  pageSize: number;
  onPageChange: (page: number) => void;
  currentPage: number;
}

export function Pagination({ total, pageSize, onPageChange, currentPage }: PaginationProps) {
  const totalPages = Math.ceil(total / pageSize);

  if (totalPages <= 1) {
    return null;
  }

  return (
    <div className="flex items-center justify-between mt-4">
      <div>
        <p className="text-sm text-gray-500">
          Showing page {currentPage} of {totalPages}
        </p>
      </div>
      <div className="flex items-center space-x-2">
        <Button
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage === 1}
        >
          Previous
        </Button>
        <Button
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage === totalPages}
        >
          Next
        </Button>
      </div>
    </div>
  );
}
