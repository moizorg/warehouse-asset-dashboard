export const CATEGORY_COLORS = [
  "#ee7b35",
  "#75a7cf",
  "#d4ac65",
  "#cb785e",
  "#78ad93",
  "#d8be4d",
];

export function buildDistribution(records) {
  const counts = records.reduce((totals, asset) => {
    totals[asset.category] = (totals[asset.category] || 0) + 1;
    return totals;
  }, {});

  return Object.entries(counts)
    .sort((left, right) => right[1] - left[1] || left[0].localeCompare(right[0]))
    .map(([category, count]) => ({ category, count }));
}
