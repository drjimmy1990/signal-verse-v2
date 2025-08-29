import { Option } from "@/components/ui/MultiSelect";

export const signalCodeOptions: Option[] = [
  { value: "W-B_23_6", label: "W-B_23_6" },
  { value: "W-S_76_4", label: "W-S_76_4" },
  { value: "B_123_6", label: "B_123_6" },
  { value: "S_123_6", label: "S_123_6" },
  { value: "S_152_8", label: "S_152_8" },
  { value: "B_152_8", label: "B_152_8" },
  { value: "S_176_4", label: "S_176_4" },
  { value: "B_176_4", label: "B_176_4" },
  { value: "T-B", label: "T-B" },
  { value: "T-S", label: "T-S" },
  { value: "FB-B", label: "FB-B" },
  { value: "FB-S", label: "FB-S" },
  { value: "S_76_4", label: "S_76_4" },
  { value: "B_23_6", label: "B_23_6" },
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