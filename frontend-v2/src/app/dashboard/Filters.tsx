
'use client';

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { MultiSelect, Option } from "@/components/ui/MultiSelect";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";

interface FiltersProps {
  filters: any;
  setFilters: any;
  onFilter: () => void;
  options: {
    scanner_type: Option[];
    timeframe: Option[];
    signal_codes: Option[];
    status: Option[];
  };
}

export function Filters({ filters, setFilters, onFilter, options }: FiltersProps) {
  return (
    <Card className="mb-6">
      <CardHeader>
        <CardTitle>Filters</CardTitle>
      </CardHeader>
      <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-400 mb-1">Symbol</label>
          <Input
            placeholder="Symbol"
            name="symbol"
            value={filters.symbol}
            onChange={(e) => setFilters({ ...filters, symbol: e.target.value })}
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-400 mb-1">Scanner Type</label>
          <MultiSelect
            placeholder="Scanner Type"
            options={options.scanner_type}
            selected={filters.scanner_type}
            onChange={(selected) => setFilters({ ...filters, scanner_type: selected })}
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-400 mb-1">Timeframe</label>
          <MultiSelect
            placeholder="Timeframe"
            options={options.timeframe}
            selected={filters.timeframe}
            onChange={(selected) => setFilters({ ...filters, timeframe: selected })}
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-400 mb-1">Status</label>
          <MultiSelect
            placeholder="Status"
            options={options.status}
            selected={filters.status}
            onChange={(selected) => setFilters({ ...filters, status: selected })}
          />
        </div>
        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-gray-400 mb-1">Signal Codes</label>
          <MultiSelect
            placeholder="Select signal codes to build a combo"
            options={options.signal_codes}
            selected={filters.signal_codes}
            onChange={(selected) => setFilters({ ...filters, signal_codes: selected })}
          />
        </div>
        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-gray-400 mb-1">Selected Combo</label>
          <div className="flex flex-wrap gap-1 p-2 border rounded min-h-[40px]">
            {filters.signal_codes.map((code: string) => (
              <Badge key={code} variant="secondary">{code}</Badge>
            ))}
          </div>
        </div>
        <div className="md:col-span-2 flex justify-end">
          <Button onClick={onFilter}>Apply Filters</Button>
        </div>
      </CardContent>
    </Card>
  );
}
