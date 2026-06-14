export function formatDate(iso: string): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (isNaN(d.getTime())) return iso;
  return d.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function truncateId(uuid: string, maxLen = 12): string {
  if (!uuid || uuid.length <= maxLen) return uuid;
  return uuid.slice(0, maxLen) + "…";
}
