import { useState, useEffect, useMemo } from "react";
import * as XLSX from "xlsx";
import { Loader2, Search, Table as TableIcon, FileSpreadsheet, Download } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

interface SpreadsheetPreviewProps {
  blob: Blob;
  downloadUrl?: string;
  filename?: string;
}

export function SpreadsheetPreview({ blob, downloadUrl, filename }: SpreadsheetPreviewProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sheets, setSheets] = useState<{ [name: string]: any[][] }>({});
  const [sheetNames, setSheetNames] = useState<string[]>([]);
  const [activeSheet, setActiveSheet] = useState<string>("");
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);

    blob
      .arrayBuffer()
      .then((buffer) => {
        if (!active) return;
        try {
          const workbook = XLSX.read(buffer, { type: "array", cellDates: true });
          if (!workbook.SheetNames || workbook.SheetNames.length === 0) {
            throw new Error("No worksheets found in this spreadsheet.");
          }

          const parsedSheets: { [name: string]: any[][] } = {};
          for (const name of workbook.SheetNames) {
            const worksheet = workbook.Sheets[name];
            const rawData = XLSX.utils.sheet_to_json<any[]>(worksheet, {
              header: 1,
              defval: "",
              raw: false,
            });
            parsedSheets[name] = rawData;
          }

          if (active) {
            setSheetNames(workbook.SheetNames);
            setSheets(parsedSheets);
            setActiveSheet(workbook.SheetNames[0]);
            setLoading(false);
          }
        } catch (err) {
          if (active) {
            console.error("Failed to parse spreadsheet:", err);
            setError(err instanceof Error ? err.message : "Failed to parse spreadsheet file");
            setLoading(false);
          }
        }
      })
      .catch((err) => {
        if (active) {
          setError(err instanceof Error ? err.message : "Failed to read document blob");
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [blob]);

  const currentData = sheets[activeSheet] || [];

  // Filter rows based on search query
  const filteredData = useMemo(() => {
    if (!searchQuery.trim()) return currentData;
    const q = searchQuery.toLowerCase();
    return currentData.filter((row, idx) => {
      // Always keep first header row
      if (idx === 0) return true;
      return row.some((cell) => String(cell ?? "").toLowerCase().includes(q));
    });
  }, [currentData, searchQuery]);

  // Determine max columns
  const maxCols = useMemo(() => {
    let max = 0;
    for (const row of currentData) {
      if (row.length > max) max = row.length;
    }
    return Math.max(max, 1);
  }, [currentData]);

  const getColLetter = (index: number) => {
    let letter = "";
    let temp = index;
    while (temp >= 0) {
      letter = String.fromCharCode((temp % 26) + 65) + letter;
      temp = Math.floor(temp / 26) - 1;
    }
    return letter;
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-2 text-muted-foreground p-8">
        <Loader2 className="h-6 w-6 animate-spin text-primary" />
        <span className="text-xs font-medium">Parsing spreadsheet data…</span>
      </div>
    );
  }

  if (error || currentData.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-3 text-muted-foreground p-8 text-center">
        <FileSpreadsheet className="h-8 w-8 text-muted-foreground/60" />
        <div className="text-xs">
          <p className="font-semibold text-foreground">Spreadsheet preview not available</p>
          <p className="text-muted-foreground mt-1">{error || "The sheet is empty"}</p>
        </div>
        {downloadUrl && (
          <Button asChild size="sm" variant="outline" className="gap-1.5 h-8 text-xs rounded-lg mt-2">
            <a href={downloadUrl} download={filename || "document.csv"}>
              <Download className="h-3.5 w-3.5" /> Download file
            </a>
          </Button>
        )}
      </div>
    );
  }

  const headerRow = filteredData[0] || [];
  const bodyRows = filteredData.slice(1);

  return (
    <div className="flex flex-col h-full w-full min-h-0 bg-background/95 rounded-xl border border-border/80 overflow-hidden shadow-sm">
      {/* Header bar: Search, Sheet tabs, metadata */}
      <div className="flex flex-wrap items-center justify-between gap-2 p-2 bg-muted/40 border-b shrink-0 text-xs">
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 font-semibold text-foreground select-none">
            <TableIcon className="h-3.5 w-3.5 text-primary" />
            <span>Spreadsheet Viewer</span>
          </div>
          <Badge variant="secondary" className="h-5 px-1.5 text-[10px] font-normal">
            {currentData.length} rows · {maxCols} cols
          </Badge>
        </div>

        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="absolute left-2 top-2 h-3.5 w-3.5 text-muted-foreground" />
            <Input
              placeholder="Search cells..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-7.5 h-7 w-36 sm:w-48 text-xs rounded-lg bg-background/90"
            />
          </div>
          {downloadUrl && (
            <Button asChild size="icon" variant="ghost" className="h-7 w-7 rounded-lg text-muted-foreground hover:text-foreground" title="Download raw file">
              <a href={downloadUrl} download={filename || "document.csv"}>
                <Download className="h-3.5 w-3.5" />
              </a>
            </Button>
          )}
        </div>
      </div>

      {/* Grid container */}
      <div className="flex-1 min-h-0 overflow-auto bg-card">
        <table className="w-full border-collapse text-xs font-sans select-text">
          <thead className="sticky top-0 z-20 bg-muted/90 backdrop-blur shadow-sm">
            {/* Column coordinate header (A, B, C, D...) */}
            <tr className="border-b border-border/70 text-[10px] text-muted-foreground font-mono">
              <th className="w-10 min-w-10 max-w-10 p-1 text-center bg-muted/90 border-r border-border/70 select-none font-semibold">
                #
              </th>
              {Array.from({ length: maxCols }).map((_, colIdx) => (
                <th
                  key={colIdx}
                  className="px-2.5 py-1 text-left bg-muted/90 border-r border-border/60 font-medium select-none min-w-[120px] max-w-[240px] truncate"
                >
                  {getColLetter(colIdx)}
                </th>
              ))}
            </tr>
            {/* Actual data header row (Row 1) */}
            <tr className="border-b border-border bg-muted/60 font-semibold text-foreground">
              <td className="p-1 text-center bg-muted/80 border-r border-border text-[10px] font-mono text-muted-foreground select-none">
                1
              </td>
              {Array.from({ length: maxCols }).map((_, colIdx) => (
                <td
                  key={colIdx}
                  className="px-2.5 py-1.5 border-r border-border/60 min-w-[120px] max-w-[240px] truncate text-xs font-semibold text-foreground/90 bg-muted/40"
                  title={String(headerRow[colIdx] ?? "")}
                >
                  {String(headerRow[colIdx] ?? "")}
                </td>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-border/40 font-mono text-[11px]">
            {bodyRows.map((row, rowIdx) => {
              const actualRowNumber = rowIdx + 2;
              return (
                <tr
                  key={rowIdx}
                  className="hover:bg-primary/5 transition-colors even:bg-muted/15"
                >
                  <td className="p-1 text-center bg-muted/30 border-r border-border/60 text-[10px] font-mono text-muted-foreground select-none font-medium">
                    {actualRowNumber}
                  </td>
                  {Array.from({ length: maxCols }).map((_, colIdx) => {
                    const cellVal = String(row[colIdx] ?? "");
                    const isHigh = cellVal.toLowerCase() === "high";
                    const isLow = cellVal.toLowerCase() === "low";
                    return (
                      <td
                        key={colIdx}
                        className={`px-2.5 py-1.5 border-r border-border/40 min-w-[120px] max-w-[240px] truncate ${
                          isHigh
                            ? "text-rose-600 font-semibold bg-rose-500/10"
                            : isLow
                            ? "text-amber-600 font-semibold bg-amber-500/10"
                            : "text-foreground"
                        }`}
                        title={cellVal}
                      >
                        {cellVal}
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Sheet tab footer if multiple sheets */}
      {sheetNames.length > 1 && (
        <div className="flex items-center gap-1 p-1 bg-muted/50 border-t shrink-0 overflow-x-auto select-none">
          {sheetNames.map((name) => (
            <button
              key={name}
              type="button"
              onClick={() => setActiveSheet(name)}
              className={`px-3 py-1 text-xs rounded font-medium transition-colors ${
                activeSheet === name
                  ? "bg-background text-primary shadow-sm border font-semibold"
                  : "text-muted-foreground hover:text-foreground hover:bg-muted"
              }`}
            >
              {name}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
