interface MetadataField {
  label: string;
  value: string | undefined;
  span?: 1 | 2;
}

interface MetadataGridProps {
  fields: MetadataField[];
}

export function MetadataGrid({ fields }: MetadataGridProps) {
  return (
    <div className="grid grid-cols-4 gap-4">
      {fields.map((f) => (
        <div key={f.label} className={f.span === 2 ? "col-span-2" : ""}>
          <dt className="text-[11px] text-text-subtle font-medium uppercase tracking-wide mb-1">
            {f.label}
          </dt>
          <dd className="text-[13px] text-text-default font-medium">
            {f.value || "—"}
          </dd>
        </div>
      ))}
    </div>
  );
}

export function patientToMetadataFields(patient: {
  dob?: string;
  gender?: string;
  phone?: string;
  mrn?: string;
  blood_type?: string;
  department?: string;
  attending_physician?: string;
  admission_status?: string;
  admitted_date?: string;
  room?: string;
}): MetadataField[] {
  return [
    { label: "Date of Birth", value: patient.dob },
    { label: "Sex", value: patient.gender },
    { label: "Phone", value: (patient as Record<string, string>).phone || "—" },
    { label: "MRN", value: patient.mrn },
    { label: "Blood Type", value: patient.blood_type },
    { label: "Department", value: patient.department },
    { label: "Attending", value: patient.attending_physician },
    { label: "Status", value: patient.admission_status },
    { label: "Admitted", value: patient.admitted_date },
    { label: "Room", value: patient.room },
  ];
}
