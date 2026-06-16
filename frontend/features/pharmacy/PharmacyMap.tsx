"use client";

import { useEffect, useRef, useState } from "react";
import { Map, AdvancedMarker, Pin, useMap, InfoWindow } from "@vis.gl/react-google-maps";
import type { Pharmacy } from "./api";

interface Props {
  userLocation: { lat: number; lng: number } | null;
  pharmacies: Pharmacy[];
}

const DEFAULT_CENTER = { lat: 37.5665, lng: 126.978 };

function MapMarkers({ userLocation, pharmacies }: Props) {
  const map = useMap();
  const userPannedRef = useRef(false);
  const prevPharmaciesRef = useRef<Pharmacy[]>([]);

  const [selectedPharmacy, setSelectedPharmacy] = useState<Pharmacy | null>(null);
  const [selectedMarker, setSelectedMarker] = useState<google.maps.marker.AdvancedMarkerElement | null>(null);

  // 위치 확인 시 지도 초기 이동 (한 번)
  useEffect(() => {
    if (map && userLocation && !userPannedRef.current) {
      map.panTo(userLocation);
      map.setZoom(15);
      userPannedRef.current = true;
    }
  }, [map, userLocation]);

  // pharmacies 변경 시 → 첫 번째 약국으로 지도 이동
  useEffect(() => {
    if (!map || pharmacies === prevPharmaciesRef.current) return;
    prevPharmaciesRef.current = pharmacies;

    setSelectedPharmacy(null);
    setSelectedMarker(null);

    const first = pharmacies.find((p) => p.lat != null && p.lng != null);
    if (first) {
      map.panTo({ lat: first.lat!, lng: first.lng! });
      map.setZoom(14);
    } else if (userLocation) {
      map.panTo(userLocation);
      map.setZoom(15);
    }
  }, [map, pharmacies, userLocation]);

  return (
    <>
      {/* 내 위치 마커 */}
      {userLocation && (
        <AdvancedMarker position={userLocation} zIndex={10}>
          <div
            style={{
              width: 18,
              height: 18,
              background: "#4285F4",
              border: "3px solid #fff",
              borderRadius: "50%",
              boxShadow: "0 2px 6px rgba(0,0,0,.35)",
            }}
          />
        </AdvancedMarker>
      )}

      {/* 약국 마커 */}
      {pharmacies
        .filter((p) => p.lat != null && p.lng != null)
        .map((p) => (
          <AdvancedMarker
            key={p.id}
            position={{ lat: p.lat!, lng: p.lng! }}
            zIndex={5}
            onClick={(e) => {
              if (selectedPharmacy?.id === p.id) {
                setSelectedPharmacy(null);
                setSelectedMarker(null);
              } else {
                setSelectedPharmacy(p);
                setSelectedMarker(e.marker);
              }
            }}
          >
            <Pin background="#F97316" borderColor="#EA580C" glyphColor="#ffffff" />
          </AdvancedMarker>
        ))}

      {/* 마커 클릭 시 약국 이름 InfoWindow */}
      {selectedPharmacy && selectedMarker && (
        <InfoWindow
          anchor={selectedMarker}
          onCloseClick={() => {
            setSelectedPharmacy(null);
            setSelectedMarker(null);
          }}
        >
          <p style={{ fontSize: 13, fontWeight: 600, margin: 0 }}>
            {selectedPharmacy.name}
          </p>
        </InfoWindow>
      )}
    </>
  );
}

// APIProvider는 page.tsx에 있음 — 이 컴포넌트는 그 안에서 렌더됨
export default function PharmacyMap({ userLocation, pharmacies }: Props) {
  return (
    <div className="mt-4 h-44 w-full overflow-hidden rounded-2xl">
      <Map
        defaultCenter={userLocation ?? DEFAULT_CENTER}
        defaultZoom={15}
        mapId="DEMO_MAP_ID"
        disableDefaultUI
        zoomControl
        style={{ width: "100%", height: "100%" }}
      >
        <MapMarkers userLocation={userLocation} pharmacies={pharmacies} />
      </Map>
    </div>
  );
}