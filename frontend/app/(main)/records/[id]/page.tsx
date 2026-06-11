"use client";

import { use } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ChevronLeft, Pencil, Trash2, FileText } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useRecord, useDeleteRecord } from "@/features/medical-records/queries";

export default function RecordDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const recordId = Number(id);
  const router = useRouter();
  const { data: record, isLoading } = useRecord(recordId);
  const del = useDeleteRecord();

  function handleDelete() {
    if (!confirm("이 진료기록을 삭제하시겠습니까?")) return;
    del.mutate(recordId, {
      onSuccess: () => router.replace("/records"),
    });
  }

  if (isLoading) {
    return (
      <main className="mx-auto w-full max-w-md px-5 py-6">
        <p className="text-sm text-muted-foreground">불러오는 중...</p>
      </main>
    );
  }

  if (!record) {
    return (
      <main className="mx-auto w-full max-w-md px-5 py-6">
        <div className="flex items-center gap-2">
          <button onClick={() => router.back()} className="p-1 text-foreground">
            <ChevronLeft className="h-6 w-6" />
          </button>
          <h1 className="text-2xl font-bold">진료기록 상세</h1>
        </div>
        <div className="mt-16 flex flex-col items-center text-muted-foreground">
          <FileText className="h-12 w-12 opacity-30" />
          <p className="mt-3 text-sm">진료기록을 찾을 수 없습니다.</p>
          <Link href="/records" className="mt-2 text-sm text-primary hover:underline">목록으로 돌아가기</Link>
        </div>
      </main>
    );
  }

  return (
    <main className="mx-auto w-full max-w-md px-5 py-6 pb-32">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <button onClick={() => router.back()} className="p-1 text-foreground">
            <ChevronLeft className="h-6 w-6" />
          </button>
          <h1 className="text-2xl font-bold">진료기록 상세</h1>
        </div>
        <div className="flex items-center gap-1">
          <Link
            href={`/records/${recordId}/edit`}
            className="flex h-9 w-9 items-center justify-center rounded-full text-muted-foreground hover:bg-accent"
            aria-label="수정"
          >
            <Pencil className="h-4 w-4" />
          </Link>
          <button
            onClick={handleDelete}
            className="flex h-9 w-9 items-center justify-center rounded-full text-muted-foreground hover:text-destructive"
            aria-label="삭제"
            disabled={del.isPending}
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </div>

      <Card className="mt-5 divide-y divide-border">
        <InfoRow label="병원명" value={record.hospital_name} />
        <InfoRow label="진료과" value={record.department} />
        <InfoRow label="방문일" value={record.visit_date} />
        <InfoRow label="진단명" value={record.diagnosis} />
      </Card>

      {record.memo && (
        <>
          <p className="mt-5 text-sm font-semibold text-muted-foreground">메모</p>
          <Card className="mt-2 p-4">
            <p className="whitespace-pre-wrap text-sm">{record.memo}</p>
          </Card>
        </>
      )}

      {record.created_at && (
        <p className="mt-4 text-right text-xs text-muted-foreground">
          등록일: {record.created_at.slice(0, 10)}
        </p>
      )}

      <div className="fixed inset-x-0 bottom-6 mx-auto max-w-md px-5">
        <Button variant="outline" className="w-full" onClick={() => router.replace("/records")}>
          목록으로
        </Button>
      </div>
    </main>
  );
}

function InfoRow({ label, value }: { label: string; value?: string }) {
  return (
    <div className="flex items-start justify-between gap-4 px-4 py-3.5">
      <span className="shrink-0 text-sm text-muted-foreground">{label}</span>
      <span className="text-right text-sm">{value || "—"}</span>
    </div>
  );
}
