import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Users } from "lucide-react";
import Link from "next/link";

interface RecentPatient {
  id: string;
  fullName: string;
  mrn: string;
  department?: string;
  lastVisit?: string;
}

interface RecentPatientsCardProps {
  patients: RecentPatient[];
}

export function RecentPatientsCard({ patients }: RecentPatientsCardProps) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-h4 flex items-center gap-2">
          <Users className="w-4 h-4 text-text-subtle" />
          Recent Patients
        </CardTitle>
      </CardHeader>
      <CardContent>
        {patients.length === 0 ? (
          <p className="text-[12px] text-text-muted py-2">No recent patients</p>
        ) : (
          <div className="space-y-1">
            {patients.map((p) => {
              const initials = p.fullName.split(" ").map((n) => n[0]).join("").toUpperCase();
              return (
                <Link
                  key={p.id}
                  href={"/patients/" + p.id}
                  className="flex items-center gap-3 py-2 px-2 rounded-lg hover:bg-bg-surface-tint transition-colors group"
                >
                  <div className="w-8 h-8 rounded-full bg-primary-100 text-primary-700 flex items-center justify-center text-[11px] font-semibold flex-shrink-0">
                    {initials}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-[13px] font-medium text-text-default truncate group-hover:text-primary-600 transition-colors">
                      {p.fullName}
                    </p>
                    <p className="text-[11px] text-text-subtle truncate">
                      MRN: {p.mrn}{p.department ? " · " + p.department : ""}
                    </p>
                  </div>
                </Link>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
