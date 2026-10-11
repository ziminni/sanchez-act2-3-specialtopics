/**
 * Shared display formatting. Grades and the computed GWA use the same two-decimal scale,
 * and a missing value is shown as an em dash rather than as zero.
 */
export const score = (value: number | null | undefined) =>
  value === null || value === undefined ? '—' : value.toFixed(2);
