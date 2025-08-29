import { Option } from "@/components/ui/MultiSelect";

export const signalCodeOptions: Option[] = [
  { value: "W-B 23.6", label: "W-B 23.6" },
  { value: "W-S 76.4", label: "W-S 76.4" },
  { value: "B 123.6", label: "B 123.6" },
  { value: "S 123.6", label: "S 123.6" },
  { value: "152.8--S", label: "152.8--S" },
  { value: "152.8--B", label: "152.8--B" },
  { value: "176.4--S", label: "176.4--S" },
  { value: "176.4--B", label: "176.4--B" },
  { value: "T-B", label: "T-B" },
  { value: "T-S", label: "T-S" },
  { value: "FB-B", label: "FB-B" },
  { value: "FB-S", label: "FB-S" },
  { value: "S 76.4", label: "S 76.4" },
  { value: "B 23.6", label: "B 23.6" },
  { value: "Bearish", label: "Bearish" },
  { value: "Bullish", label: "Bullish" },
];

export const statusOptions: Option[] = [
  { value: "active", label: "active" },
  { value: "confirmed", label: "confirmed" },
  { value: "invalidated", label: "invalidated" },
];

export const timeframeOptions: Option[] = [
    { value: "15m", label: "15m" },
    { value: "1h", label: "1h" },
    { value: "4h", label: "4h" },
    { value: "1d", label: "1d" },
];

export const scannerTypeOptions: Option[] = [
    { value: "fawda", label: "fawda" },
];
