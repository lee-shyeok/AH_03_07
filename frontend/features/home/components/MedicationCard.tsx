import { Check, Circle } from "lucide-react";
import SectionCard from "./SectionCard";

export interface Medication {
  label: string;
  done: boolean;
}

interface MedicationCardProps {
  medications: Medication[];
  moreHref?: string;
  accentClassName?: string;
}

export default function MedicationCard({
  medications,
  moreHref = "/medication/checklist",
  accentClassName = "text-primary",
}: MedicationCardProps) {
  return (
    <SectionCard title="오늘 복약" moreHref={moreHref} accentClassName={accentClassName}>
      <ul className="mt-3 space-y-2">
        {medications.map((m, i) => (
          <li key={i} className="flex items-center gap-2.5 text-sm">
            {m.done ? (
              <Check className={`h-4 w-4 ${accentClassName}`} />
            ) : (
              <Circle className="h-4 w-4 text-muted-foreground/40" />
            )}
            <span className={m.done ? "text-foreground" : "text-muted-foreground"}>
              {m.label}
            </span>
          </li>
        ))}
      </ul>
    </SectionCard>
  );
}