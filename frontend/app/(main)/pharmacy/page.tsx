"use client";

import { useState, useEffect, useRef } from "react";
import dynamic from "next/dynamic";
import { useRouter } from "next/navigation";
import { Search, Store, Clock, Phone, ArrowLeft, MapPin } from "lucide-react";
import { Card } from "@/components/ui/card";
import { APIProvider, useMapsLibrary } from "@vis.gl/react-google-maps";
import type { Pharmacy } from "@/features/pharmacy/api";

const PharmacyMap = dynamic(
  () => import("@/features/pharmacy/PharmacyMap"),
  { ssr: false }
);

const API_KEY = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY ?? "";

function haversine(
  from: { lat: number; lng: number },
  to: { lat: number; lng: number }
): string {
  const R = 6371000;
  const toRad = (x: number) => (x * Math.PI) / 180;
  const dLat = toRad(to.lat - from.lat);
  const dLng = toRad(to.lng - from.lng);
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(from.lat)) * Math.cos(toRad(to.lat)) * Math.sin(dLng / 2) ** 2;
  const d = 2 * R * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return d < 1000 ? `${Math.round(d)}m` : `${(d / 1000).toFixed(1)}km`;
}

function mapPlace(
  place: google.maps.places.PlaceResult,
  index: number,
  userLocation: { lat: number; lng: number } | null
): Pharmacy {
  const lat = place.geometry?.location?.lat();
  const lng = place.geometry?.location?.lng();
  return {
    id: index + 1,
    name: place.name ?? "",
    address: place.vicinity ?? place.formatted_address ?? "",
    phone: place.formatted_phone_number ?? "",
    lat,
    lng,
    open: place.opening_hours?.isOpen() ?? undefined,
    is24h: /24/.test(place.name ?? ""),
    distance:
      userLocation && lat != null && lng != null
        ? haversine(userLocation, { lat, lng })
        : undefined,
  };
}

// ─── 실제 페이지 콘텐츠 (APIProvider 안에서 렌더) ─────────────────────────────
function PharmacyContent() {
  const router = useRouter();
  const placesLib = useMapsLibrary("places");

  const [pharmacies, setPharmacies] = useState<Pharmacy[]>([]);
  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState(false);
  const [query, setQuery] = useState("");
  const [userLocation, setUserLocation] = useState<{
    lat: number;
    lng: number;
  } | null>(null);
  const [noLocation, setNoLocation] = useState(false);

  const baseRef = useRef<Pharmacy[]>([]);
  const serviceRef = useRef<google.maps.places.PlacesService | null>(null);

  // PlacesService 초기화 (placesLib 로드 후)
  useEffect(() => {
    if (!placesLib) return;
    serviceRef.current = new placesLib.PlacesService(
      document.createElement("div")
    );
  }, [placesLib]);

  // 현재 위치 획득
  useEffect(() => {
    const isHttp = window.location.protocol !== "https:";
    if (!navigator.geolocation || isHttp) {
      setNoLocation(true);
      setLoading(false);
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setUserLocation({
          lat: pos.coords.latitude,
          lng: pos.coords.longitude,
        });
      },
      () => {
        setNoLocation(true);
        setLoading(false);
      },
      { timeout: 10000 }
    );
  }, []);

  // 주변 약국 검색 (위치 + Places 준비 완료 시)
  useEffect(() => {
    if (!placesLib || !serviceRef.current || !userLocation) return;

    let stale = false;

    serviceRef.current.nearbySearch(
      { location: userLocation, radius: 2000, type: "pharmacy" },
      (results, status) => {
        if (stale) return;
        setLoading(false);
        if (status === placesLib.PlacesServiceStatus.OK && results) {
          const list = results.map((p, i) => mapPlace(p, i, userLocation));
          baseRef.current = list;
          setPharmacies(list);
        } else {
          baseRef.current = [];
          setPharmacies([]);
        }
      }
    );

    return () => {
      stale = true;
    };
  }, [placesLib, userLocation]);

  // 키워드 검색
  useEffect(() => {
    if (!query.trim()) {
      setPharmacies(baseRef.current);
      return;
    }
    if (!placesLib || !serviceRef.current) return;

    let stale = false;

    const timer = setTimeout(() => {
      setSearching(true);

      const callback = (
        results: google.maps.places.PlaceResult[] | null,
        status: string
      ) => {
        if (stale) return;
        setSearching(false);
        if (status === placesLib.PlacesServiceStatus.OK && results) {
          setPharmacies(results.map((p, i) => mapPlace(p, i, userLocation)));
        } else {
          setPharmacies([]);
        }
      };

      if (userLocation) {
        serviceRef.current!.textSearch(
          { query: query.trim() + " 약국", location: userLocation, radius: 5000 },
          callback
        );
      } else {
        serviceRef.current!.textSearch(
          { query: query.trim() + " 약국" },
          callback
        );
      }
    }, 400);

    return () => {
      stale = true;
      clearTimeout(timer);
    };
  }, [query, placesLib, userLocation]);

  return (
    <main className="mx-auto w-full max-w-md px-5 py-8">
      {/* 헤더 */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => router.push("/home")}
          className="flex h-8 w-8 items-center justify-center rounded-full hover:bg-muted"
          aria-label="뒤로가기"
        >
          <ArrowLeft className="h-5 w-5" />
        </button>
        <h1 className="text-xl font-bold">약국 찾기</h1>
      </div>

      {/* 검색바 */}
      <div className="mt-5 flex items-center gap-2 rounded-full border border-border bg-card px-4 py-3">
        <Search className="h-4 w-4 text-muted-foreground" />
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="약국 이름·지역 검색"
          className="flex-1 bg-transparent text-sm outline-none"
        />
      </div>

      {/* 지도 */}
      <PharmacyMap userLocation={userLocation} pharmacies={pharmacies} />

      {/* 위치 권한 없음 안내 */}
      {noLocation && (
        <div className="mt-3 flex items-center gap-2 rounded-xl bg-yellow-50 px-4 py-3 text-sm text-yellow-700">
          <MapPin className="h-4 w-4 shrink-0" />
          <span>위치 권한을 허용하면 주변 약국을 표시합니다.</span>
        </div>
      )}

      {/* 목록 헤더 */}
      <div className="mt-6">
        <p className="font-bold">
          {query.trim() ? "검색 결과" : "내 주변 약국"}{" "}
          {!loading && !searching && (
            <span className="text-primary">{pharmacies.length}</span>
          )}
        </p>
      </div>

      {(loading || searching) && (
        <div className="mt-8 flex justify-center">
          <p className="text-sm text-muted-foreground">
            {loading ? "위치 정보를 불러오는 중…" : "검색 중…"}
          </p>
        </div>
      )}

      <div className="mt-3 space-y-3">
        {pharmacies.map((p) => (
          <a
            key={p.id}
            href={`https://map.kakao.com/?q=${encodeURIComponent(p.name)}`}
            target="_blank"
            rel="noopener noreferrer"
          >
            <Card className="flex items-start gap-3 p-4">
              {/* 아이콘 */}
              <div
                className={
                  "flex h-11 w-11 shrink-0 items-center justify-center rounded-xl " +
                  (p.open ? "bg-secondary" : "bg-muted")
                }
              >
                {p.is24h ? (
                  <Clock
                    className={
                      "h-6 w-6 " +
                      (p.open ? "text-primary" : "text-muted-foreground")
                    }
                  />
                ) : (
                  <Store
                    className={
                      "h-6 w-6 " +
                      (p.open ? "text-primary" : "text-muted-foreground")
                    }
                  />
                )}
              </div>

              {/* 정보 */}
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-1.5">
                  <p className="font-bold">{p.name}</p>
                  {p.open !== undefined && (
                    <span
                      className={
                        "rounded-md px-1.5 py-0.5 text-[11px] font-semibold " +
                        (p.open
                          ? "bg-secondary text-primary"
                          : "bg-muted text-muted-foreground")
                      }
                    >
                      {p.open ? "영업중" : "영업종료"}
                    </span>
                  )}
                  {p.is24h && (
                    <span className="rounded-md bg-blue-50 px-1.5 py-0.5 text-[11px] font-semibold text-blue-500">
                      24시
                    </span>
                  )}
                  {p.isNight && !p.is24h && (
                    <span className="rounded-md bg-indigo-50 px-1.5 py-0.5 text-[11px] font-semibold text-indigo-500">
                      야간
                    </span>
                  )}
                </div>

                <p className="mt-0.5 truncate text-xs text-muted-foreground">
                  {p.distance ? `${p.distance} · ` : ""}
                  {p.address}
                </p>

                {p.hours && (
                  <p className="mt-0.5 flex items-center gap-1 text-xs text-muted-foreground">
                    <Clock className="h-3 w-3" />
                    {p.hours}
                  </p>
                )}

                {p.phone && (
                  <p className="mt-0.5 flex items-center gap-1 text-xs text-muted-foreground">
                    <Phone className="h-3 w-3" />
                    {p.phone}
                  </p>
                )}
              </div>
            </Card>
          </a>
        ))}

        {!loading && !searching && pharmacies.length === 0 && !noLocation && (
          <p className="mt-6 text-center text-sm text-muted-foreground">
            검색 결과가 없습니다.
          </p>
        )}
      </div>
    </main>
  );
}

// ─── 진입점: API 키 확인 후 APIProvider로 감싸기 ──────────────────────────────
export default function PharmacyPage() {
  if (!API_KEY) {
    return (
      <main className="mx-auto w-full max-w-md px-5 py-20 text-center">
        <p className="text-sm text-muted-foreground">
          Google Maps API 키가 설정되지 않았습니다.
        </p>
      </main>
    );
  }

  return (
    <APIProvider apiKey={API_KEY}>
      <PharmacyContent />
    </APIProvider>
  );
}
