import type { ReactNode } from "react";
import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { Card } from "@/components/ui/card";

interface SectionCardProps {
  title?: string;
  children: ReactNode;
  moreHref?: string;
  moreLabel?: string;
  accentClassName?: string;
  className?: string;
}

export default function SectionCard({
  title,
  children,
  moreHref,
  moreLabel = "전체 보기",
  accentClassName = "text-primary",
  className = "",
}: SectionCardProps) {
  return (
    <Card className={`p-5 ${className}`}>
      {title && <h2 className="text-base font-bold">{title}</h2>}
      {children}
      {moreHref && (
        <Link
          href={moreHref}
          className={`mt-3 flex items-center justify-end gap-1 text-sm ${accentClassName}`}
        >
          {moreLabel}
          <ArrowRight className="h-3.5 w-3.5" />
        </Link>
      )}
    </Card>
  );
}