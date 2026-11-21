export const CATEGORY_COLORS = [
  "#4F8CFF",
  "#36B37E",
  "#E6A93A",
  "#D96C75",
  "#8B74D6",
  "#39A9C9",
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
