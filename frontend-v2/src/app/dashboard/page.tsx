
'use client';

import { Filters } from './Filters';
import { DataTable } from './DataTable';
import { Pagination } from './Pagination';
import { useEffect, useState } from 'react';
import { supabase } from '@/lib/supabaseClient';
import { Option } from '@/components/ui/MultiSelect';
import { ErrorDisplay } from './ErrorDisplay';
import { NoSignalsDisplay } from './NoSignalsDisplay';
import { signalCodeOptions, statusOptions, timeframeOptions, scannerTypeOptions } from '@/lib/filter-options';

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
}

export default function DashboardPage() {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState({
    symbol: '',
    scanner_type: [],
    timeframe: [],
    signal_codes: [],
    status: [],
  });
  const [options, setOptions] = useState({
    scanner_type: scannerTypeOptions,
    timeframe: timeframeOptions,
    signal_codes: signalCodeOptions,
    status: statusOptions,
  });
  const [page, setPage] = useState(1);
  const pageSize = 20;
  const [total, setTotal] = useState(0);

  const fetchSignals = async () => {
    setLoading(true);
    let query = supabase
      .from('signals')
      .select('*', { count: 'exact' })
      .order('candle_timestamp', { ascending: false })
      .range((page - 1) * pageSize, page * pageSize - 1);

    if (filters.symbol) {
      query = query.ilike('symbol', `%${filters.symbol}%`);
    }
    if (filters.scanner_type.length > 0) {
      query = query.in('scanner_type', filters.scanner_type);
    }
    if (filters.timeframe.length > 0) {
      query = query.in('timeframe', filters.timeframe);
    }
    if (filters.signal_codes.length > 0) {
      query = query.contains('signal_codes', filters.signal_codes);
    }
    if (filters.status.length > 0) {
      query = query.in('status', filters.status);
    }

    const { data, error, count } = await query;

    if (error) {
      console.error('Error fetching signals:', error);
      setError("Failed to fetch signals. Please try again later.");
    } else {
      setSignals(data as Signal[]);
      setTotal(count || 0);
      setError(null);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchSignals();

    const channel = supabase
      .channel('signals-changes')
      .on(
        'postgres_changes',
        { event: 'INSERT', schema: 'public', table: 'signals' },
        (payload: { new: Signal }) => {
          // Simple approach: refetch the first page to show the new signal
          if (page === 1) {
            fetchSignals();
          }
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [page]);

  return (
    <div className="container mx-auto py-10">
      <h1 className="text-3xl font-bold mb-6">Signal-verse Dashboard</h1>
      <Filters filters={filters} setFilters={setFilters} onFilter={fetchSignals} options={options} />
      {loading ? (
        <p>Loading...</p> // Replace with a proper skeleton loader later
      ) : error ? (
        <ErrorDisplay message={error} />
      ) : signals.length === 0 ? (
        <NoSignalsDisplay />
      ) : (
        <>
          <DataTable signals={signals} loading={loading} />
          <Pagination total={total} pageSize={pageSize} onPageChange={setPage} currentPage={page} />
        </>
      )}
    </div>
  );
}
