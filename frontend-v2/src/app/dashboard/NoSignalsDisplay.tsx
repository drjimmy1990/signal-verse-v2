'use client';

import { Info } from "lucide-react";

export function NoSignalsDisplay() {
  return (
    <div className="bg-gray-800 border border-gray-700 text-gray-400 px-4 py-10 rounded-lg text-center">
      <Info className="w-12 h-12 mx-auto mb-4 text-gray-500" />
      <h3 className="text-xl font-semibold mb-2">No Signals Found</h3>
      <p>Try adjusting your filters or check back later for new signals.</p>
    </div>
  );
}
