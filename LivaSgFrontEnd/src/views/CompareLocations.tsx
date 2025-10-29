import React, { useRef, useState, useEffect } from 'react';
import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
} from 'chart.js';
import { Radar } from 'react-chartjs-2';

ChartJS.register(RadialLinearScale, PointElement, LineElement, Filler, Tooltip, Legend);

interface LocationResult {
  id: number;
  street: string;
  area: string;
  district: string;
  priceRange: [number, number];
  avgPrice: number;
  facilities: string[];
  description: string;
  growth: number;
  amenities: string[];
  transitScore: number;
  schoolScore: number;
  amenitiesScore: number;
}

interface Props {
  locations: LocationResult[];
  onClose: () => void;
}

const formatPrice = (price: number) => {
  if (price >= 1000000) {
    return `$${(price / 1000000).toFixed(1)}M`;
  }
  return `$${(price / 1000).toFixed(0)}K`;
};

export default function CompareLocations({ locations, onClose }: Props) {
  const labels = ['Affordability', 'Accessibility', 'Amenities', 'Environment', 'Community'];

  // limit to up to 5 locations
  const maxLocations = 5;
  const locs = locations ? locations.slice(0, maxLocations) : [];

  // fetched breakdowns keyed by location id
  const [breakdowns, setBreakdowns] = useState<Record<number, Record<string, number>>>({});

  // Fetch breakdown scores for each provided location from backend:
  useEffect(() => {
    let cancelled = false;
    if (!locs.length) return;
    (async () => {
      const map: Record<number, Record<string, number>> = {};
      await Promise.all(
        locs.map(async (loc) => {
          try {
            // Prefer loc.street or loc.area as identifier
            const name = encodeURIComponent(loc.street || loc.area || String(loc.id));
            const res = await fetch(`http://localhost:8000/details/${name}/breakdown`);
            if (!res.ok) {
              console.warn('breakdown fetch failed', res.status, loc.street);
              return;
            }
            const json = await res.json().catch(() => null);
            const scores = json && (json.scores || json) ? (json.scores || json) : null;
            if (scores && typeof scores === 'object') {
              // Normalize keys (keep as numbers)
              const normalized: Record<string, number> = {};
              Object.keys(scores).forEach(k => {
                const v = Number(scores[k]);
                if (!Number.isNaN(v)) normalized[k] = v;
              });
              map[loc.id] = normalized;
            } else {
              console.warn('Unexpected breakdown payload for', loc.street, json);
            }
          } catch (err) {
            console.warn('Failed to fetch breakdown for', loc.street, err);
          }
        })
      );
      if (!cancelled) setBreakdowns(map);
    })();
    return () => { cancelled = true; };
  }, [locations]);

  // Normalizers across selected locations
  const growthVals = locs.map((l: LocationResult) => Number(l.growth) || 0);
  const growthMin = growthVals.length ? Math.min(...growthVals) : 0;
  const growthMax = growthVals.length ? Math.max(...growthVals) : 1;

  const priceVals = locs.map((l: LocationResult) => l.avgPrice || 0);
  const priceMin = priceVals.length ? Math.min(...priceVals) : 0;
  const priceMax = priceVals.length ? Math.max(...priceVals) : 1;

  const paletteBg = [
    'rgba(99,102,241,0.22)',
    'rgba(16,185,129,0.18)',
    'rgba(59,130,246,0.18)',
    'rgba(234,88,12,0.16)',
    'rgba(168,85,247,0.16)',
  ];
  const paletteBorder = [
    'rgba(99,102,241,1)',
    'rgba(16,185,129,1)',
    'rgba(59,130,246,1)',
    'rgba(234,88,12,1)',
    'rgba(168,85,247,1)',
  ];

  const clamp100 = (v: number) => Math.max(0, Math.min(100, Math.round(v)));

  // Build chart datasets using breakdowns when available; breakdown values expected as 0..1 floats.
  const data = {
    labels,
    datasets: locs.map((loc: LocationResult, i: number) => {
      const bd = breakdowns[loc.id];
      let values: number[] = [];
      if (bd) {
        // attempt to read keys with possible capitalization variants
        const getVal = (key: string) => {
          return bd[key] ?? bd[key.toLowerCase()] ?? bd[key.charAt(0).toUpperCase() + key.slice(1)] ?? null;
        };
        const a = getVal('Affordability');
        const b = getVal('Accessibility');
        const c = getVal('Amenities');
        const d = getVal('Environment');
        const e = getVal('Community');
        values = [
          a != null ? clamp100(Number(a) * 100) : 0,
          b != null ? clamp100(Number(b) * 100) : 0,
          c != null ? clamp100(Number(c) * 100) : 0,
          d != null ? clamp100(Number(d) * 100) : 0,
          e != null ? clamp100(Number(e) * 100) : 0,
        ];
      } else {
        // fallback: synthesize values from existing fields (best-effort)
        const transit = Number(loc.transitScore) || 0;
        const schools = Number(loc.schoolScore) || 0;
        const amenities = Number(loc.amenitiesScore) || 0;
        const growth = Number(loc.growth) || 0;
        const avgPrice = Number(loc.avgPrice) || 0;
        // map to the new label order: Affordability(inverse price), Accessibility(transit), Amenities, nvironment(growth inverse), Community(schools)
        const affordability = clamp100(100 - Math.round(((avgPrice - priceMin) / (priceMax - priceMin || 1)) * 100));
        const accessibility = clamp100(Math.round((transit / Math.max(1, transit)) * 100)); // best-effort, eeps within 0-100
        const amenitiesScore = clamp100(Math.round(Math.max(0, Math.min(100, amenities))));
        const environment = clamp100(100 - Math.round(((growth - growthMin) / (growthMax - growthMin || 1)) * 100));
        const community = clamp100(Math.round(Math.max(0, Math.min(100, schools))));
        values = [affordability, accessibility, amenitiesScore, environment, community];
      }

      return {
        label: loc.street,
        data: values,
        backgroundColor: paletteBg[i % paletteBg.length],
        borderColor: paletteBorder[i % paletteBorder.length],
        borderWidth: 2,
        pointBackgroundColor: paletteBorder[i % paletteBorder.length],
      };
    }),
  };

  // Debug / validation: log props and generated datasets so you can inspect in devtools
  useEffect(() => {
    console.log('CompareLocations.props.locations:', locations);
    console.log('derived locs:', locs);
    console.log('breakdowns fetched:', breakdowns);
    console.log('chart data.datasets:', data.datasets);
    // validate required numeric fields
    const invalid = locs.filter(l =>
      typeof l.transitScore !== 'number' ||
      typeof l.schoolScore !== 'number' ||
      typeof l.amenitiesScore !== 'number' ||
      typeof l.avgPrice !== 'number' ||
      typeof l.growth !== 'number'
    );
    if (invalid.length) {
      console.warn('CompareLocations: some locations missing numeric fields', invalid);
    }
  }, [locations, locs, data]);

  // Guard: show fallback if no locations supplied
  if (!locs.length) {
    return (
      <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black bg-opacity-20">
        <div className="bg-white p-6 rounded-lg">No locations provided to compare — select at least one.</div>
      </div>
    );
  }

  const options = {
    scales: {
      r: {
        suggestedMin: 0,
        suggestedMax: 100,
        ticks: { stepSize: 20, color: '#6b21a8' },
        pointLabels: { color: '#6b21a8', font: { size: 12 }, padding: 14 },
        grid: { color: 'rgba(79,70,229,0.1)' },
      },
    },
    plugins: {
      legend: { position: 'top' as const },
      tooltip: { enabled: true },
    },
    maintainAspectRatio: false,
  };

  // Drag / animation state
  const [dragY, setDragY] = useState(0); // px
  const [isDragging, setIsDragging] = useState(false);
  const [visible, setVisible] = useState(false); // used to trigger initial slide-up
  const startYRef = useRef(0);
  const modalRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    // trigger entrance animation on mount
    requestAnimationFrame(() => setVisible(true));
  }, []);

  const handlePointerDown = (e: React.PointerEvent) => {
    (e.currentTarget as Element & { setPointerCapture?: (id: number) => void })
      .setPointerCapture?.(e.pointerId);
    setIsDragging(true);
    startYRef.current = e.clientY;
  };

  const handlePointerMove = (e: React.PointerEvent) => {
    if (!isDragging) return;
    const delta = Math.max(0, e.clientY - startYRef.current);
    setDragY(delta);
  };

  const handlePointerUp = (e?: React.PointerEvent) => {
    if (e) {
      try {
        (e.currentTarget as Element & { releasePointerCapture?: (id: number) => void })
          .releasePointerCapture?.(e.pointerId);
      } catch {}
    }
    setIsDragging(false);
    const threshold = 120; // px to dismiss
    if (dragY > threshold) {
      // animate out quickly then close
      setDragY(window.innerHeight); // push out
      setTimeout(() => onClose(), 180);
      return;
    }
    // snap back
    setDragY(0);
  };

  // compute inline transform & transition
  const sheetTranslate = visible ? `translateY(${dragY}px)` : 'translateY(100%)';
  const transitionStyle = isDragging ? 'none' : 'transform 220ms cubic-bezier(.2,.9,.2,1)';

  // overlay opacity should fade as sheet is pulled down
  const modalMaxHeight = (typeof window !== 'undefined') ? window.innerHeight * 0.9 : 800;
  const baseOverlayOpacity = 0.45;
  const dragFactor = Math.max(0, 1 - dragY / modalMaxHeight);
  // when not visible overlay is fully transparent; when visible scale by drag factor
  const overlayOpacity = visible ? baseOverlayOpacity * dragFactor : 0;
  const overlayTransition = isDragging ? 'none' : 'opacity 320ms cubic-bezier(0.2,0.9,0.2,1)';

  return (
    <div
      className="fixed inset-0 z-[100] flex items-end justify-center"
      // overlay click closes
      onClick={() => {
        // if user taps overlay, close
        onClose();
      }}
      aria-hidden
    >
      {/* Greyed overlay */}
      <div
        className="absolute inset-0 bg-black z-40"
        style={{ opacity: overlayOpacity, transition: overlayTransition }}
      />

      {/* Styles for keyframes and handle */}
      <style>{`
        @keyframes slideUp {
          0% { transform: translateY(100%); }
          100% { transform: translateY(0%); }
        }
        .sheet {
          animation-fill-mode: forwards;
        }
        .sheet.enter {
          animation: slideUp 420ms cubic-bezier(0.2,0.9,0.2,1);
        }
        .drag-handle {
          width: 48px;
          height: 6px;
          border-radius: 9999px;
          background: rgba(107,21,168,0.18);
          margin-top: 8px;
          margin-bottom: 8px;
        }
      `}</style>

      {/* Modal sheet: anchored bottom, 90% height */}
      <div
        ref={modalRef}
        className={`sheet ${visible ? 'enter' : ''} bg-white rounded-t-2xl z-50`}
        onClick={(e) => e.stopPropagation()}
        style={{
          width: '90vw',
          maxWidth: '90vw',
          height: '90vh',
          maxHeight: '90vh',
          transform: visible && dragY === 0 ? undefined : sheetTranslate,
          transition: visible ? transitionStyle : undefined,
          borderTopLeftRadius: 16,
          borderTopRightRadius: 16,
          overflow: 'hidden',
          touchAction: 'none', // allow pointer events for dragging
        }}
      >
        {/* pull bar area: pointer handlers attached here */}
        <div
          className="w-full flex items-center justify-center cursor-grab select-none"
          onPointerDown={handlePointerDown}
          onPointerMove={handlePointerMove}
          onPointerUp={handlePointerUp}
          onPointerCancel={handlePointerUp}
        >
          <div className="drag-handle" />
        </div>

        {/* Content area */}
        <div className="p-4 h-[calc(100%-40px)] overflow-auto flex flex-col">
          {/* Square purple container with centered radar */}
          <div
            className="bg-purple-50 p-4 rounded-xl w-full max-w-full mx-auto relative overflow-visible flex-none"
            style={{ maxHeight: 'min(70vh, 90vw)', aspectRatio: '1 / 1' }}
          >
            <div className="absolute inset-0 flex items-center justify-center p-2">
              <div className="w-full h-full">
                <Radar
                  data={data}
                  options={{ ...options, responsive: true, maintainAspectRatio: false }}
                  style={{ width: '100%', height: '100%' }}
                />
              </div>
            </div>
          </div>

          {/* Summary cards for selected locations (up to 5) */}
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4 mt-4">
            {locs.map((loc) => (
              <div key={loc.id} className="p-3 bg-white rounded-lg border border-gray-100">
                <div className="font-semibold text-purple-900">{loc.street}</div>
                <div className="text-sm text-purple-700">{loc.area}, {loc.district}</div>
                <div className="text-sm text-purple-600 mt-2">
                  Avg Price: {formatPrice(loc.priceRange[0])} - {formatPrice(loc.priceRange[1])}
                </div>
                <div className="text-sm text-green-600 font-semibold mt-1">+{loc.growth}% Growth</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}