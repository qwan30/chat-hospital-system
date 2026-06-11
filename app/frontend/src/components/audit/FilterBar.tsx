import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Search } from "lucide-react";
import { useState } from "react";

export function FilterBar() {
  const [search, setSearch] = useState("");
  const [action, setAction] = useState("all");
  const [result, setResult] = useState("all");

  return (
    <div className="flex items-center gap-3">
      <div className="relative w-48"><Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-text-subtle" /><Input placeholder="Search..." className="pl-8 text-[13px] h-9" value={search} onChange={(e) => setSearch(e.target.value)} /></div>
      <Select value={action} onValueChange={setAction}><SelectTrigger className="w-[130px] h-9 text-[13px]"><SelectValue placeholder="Action" /></SelectTrigger><SelectContent><SelectItem value="all">All Actions</SelectItem><SelectItem value="read">Read</SelectItem><SelectItem value="write">Write</SelectItem><SelectItem value="delete">Delete</SelectItem></SelectContent></Select>
      <Select value={result} onValueChange={setResult}><SelectTrigger className="w-[120px] h-9 text-[13px]"><SelectValue placeholder="Result" /></SelectTrigger><SelectContent><SelectItem value="all">All Results</SelectItem><SelectItem value="allow">Allowed</SelectItem><SelectItem value="deny">Denied</SelectItem></SelectContent></Select>
      <Button variant="outline" size="sm" className="h-9" onClick={() => { /* trigger filter */ }}>Filters</Button>
    </div>
  );
}
