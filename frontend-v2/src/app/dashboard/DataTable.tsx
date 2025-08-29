
'use client';

import {
  Table,
  TableHeader,
  TableRow,
  TableHead,
  TableBody,
  TableCell,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";

// Define the type for a signal based on the schema
interface Signal {
  id: string;
  symbol: string;
  scanner_type: string;
  timeframe: string;
  status: string;
  entry_price: number | null;
  candle_timestamp: string;
  signal_codes: string[];
  hadena_timestamp: string | null;
  metadata: string | {
    hadena_type?: string;
  } | null;
}

export function DataTable({ signals, loading }: { signals: Signal[], loading: boolean }) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Symbol</TableHead>
          <TableHead>Scanner Type</TableHead>
          <TableHead>Timeframe</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Entry Price</TableHead>
          <TableHead>Signal Codes</TableHead>
          <TableHead>Candle Timestamp</TableHead>
          <TableHead>Hadena Type</TableHead>
          <TableHead>Hadena Timestamp</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {loading ? (
          <TableRow>
            <TableCell colSpan={9} className="text-center">
              Loading...
            </TableCell>
          </TableRow>
        ) : signals.length > 0 ? (
          signals.map((signal) => (
            <TableRow key={signal.id}>
              <TableCell>{signal.symbol}</TableCell>
              <TableCell>{signal.scanner_type}</TableCell>
              <TableCell>{signal.timeframe}</TableCell>
              <TableCell>
                <span
                  className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                    signal.status === "active"
                      ? "bg-green-900 text-green-200"
                      : signal.status === "confirmed"
                      ? "bg-yellow-900 text-yellow-200"
                      : "bg-red-900 text-red-200"
                  }`}
                >
                  {signal.status}
                </span>
              </TableCell>
              <TableCell>{signal.entry_price}</TableCell>
              <TableCell>
                <div className="flex flex-wrap gap-1">
                  {signal.signal_codes.map(code => (
                    <Badge key={code} variant="secondary">{code}</Badge>
                  ))}
                </div>
              </TableCell>
              <TableCell>{new Date(signal.candle_timestamp).toLocaleString()}</TableCell>
              <TableCell>
                {(() => {
                  if (!signal.metadata) return 'N/A';
                  try {
                    const meta = typeof signal.metadata === 'string'
                      ? JSON.parse(signal.metadata)
                      : signal.metadata;
                    return meta?.hadena_type ?? 'N/A';
                  } catch {
                    return 'Error';
                  }
                })()}
              </TableCell>
              <TableCell>{signal.hadena_timestamp ? new Date(signal.hadena_timestamp).toLocaleString() : 'N/A'}</TableCell>
            </TableRow>
          ))
        ) : (
          <TableRow>
            <TableCell colSpan={9} className="text-center">
              No data available.
            </TableCell>
          </TableRow>
        )}
      </TableBody>
    </Table>
  );
}
