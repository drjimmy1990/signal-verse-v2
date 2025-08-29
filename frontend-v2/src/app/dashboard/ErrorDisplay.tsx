'use client';

import { AlertTriangle } from "lucide-react";

export function ErrorDisplay({ message }: { message: string }) {
  return (
    <div className="bg-red-900 border border-red-700 text-red-200 px-4 py-3 rounded-lg relative flex items-center">
      <AlertTriangle className="w-5 h-5 mr-2" />
      <div>
        <strong className="font-bold">Error:</strong>
        <span className="block sm:inline ml-2">{message}</span>
      </div>
    </div>
  );
}
