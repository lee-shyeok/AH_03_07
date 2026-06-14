"use client";

import { useEffect, useRef } from "react";
import { Map, AdvancedMarker, Pin, useMap } from "@vis.gl/react-google-maps";
import type { Pharmacy } from "./api";

interface Props {
  userLocation: { lat: number; lng: number } | null;
  pharmacies: Pharmacy[];
}

const DEFAULT_CENTER = { lat: 37.5665, lng: 126.978 };

function MapMarkers({ userLocation, pharmacies }: Props) {
  const map = useMap();
  const pannedRef = useRef(false);

  useEffect(() => {
    if (map && userLocation && !pannedRef.current) {
      map.panTo(userLocation);
      pannedRef.current = true;
    }
  }, [map, userLocation]);

  return (
    <>
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
      {pharmacies
        .filter((p) => p.lat != null && p.lng != null)
        .map((p) => (
          <AdvancedMarker
            key={p.id}
            position={{ lat: p.lat!, lng: p.lng! }}
            title={p.name}
          >
            <Pin
              background="#F97316"
              borderColor="#EA580C"
              glyphColor="#ffffff"
            />
          </AdvancedMarker>
        ))}
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