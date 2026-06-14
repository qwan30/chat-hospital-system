"use client";

import { Search, Filter } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export interface PatientSearchToolbarProps {
  query: string;
  onQueryChange: (q: string) => void;
  department: string;
  onDepartmentChange: (d: string) => void;
  status: string;
  onStatusChange: (s: string) => void;
}

export function PatientSearchToolbar({
  query,
  onQueryChange,
  department,
  onDepartmentChange,
  status,
  onStatusChange,
}: PatientSearchToolbarProps) {
  return (
    <div className="flex items-center gap-3">
      <div className="relative flex-1 max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-subtle" />
        <Input
          placeholder="Search by name, MRN..."
          value={query}
          onChange={(e) => onQueryChange(e.target.value)}
          className="pl-9"
        />
      </div>
      <Select value={department} onValueChange={onDepartmentChange}>
        <SelectTrigger className="w-[160px]">
          <SelectValue placeholder="Department" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Departments</SelectItem>
          <SelectItem value="Cardiology">Cardiology</SelectItem>
          <SelectItem value="Neurology">Neurology</SelectItem>
          <SelectItem value="Oncology">Oncology</SelectItem>
          <SelectItem value="Pediatrics">Pediatrics</SelectItem>
        </SelectContent>
      </Select>
      <Select value={status} onValueChange={onStatusChange}>
        <SelectTrigger className="w-[140px]">
          <SelectValue placeholder="Status" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Statuses</SelectItem>
          <SelectItem value="active">Active</SelectItem>
          <SelectItem value="admitted">Admitted</SelectItem>
          <SelectItem value="discharged">Discharged</SelectItem>
          <SelectItem value="observation">Observation</SelectItem>
        </SelectContent>
      </Select>
      <Button variant="outline" className="gap-2">
        <Filter className="w-4 h-4" />
        Filters
      </Button>
    </div>
  );
}
