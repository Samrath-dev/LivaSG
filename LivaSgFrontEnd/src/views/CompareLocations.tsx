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

// ...existing code...

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
  const labels = ['Transit', 'Schools', 'Amenities', 'Growth', 'Affordability'];

  // limit to up to 5 locations
  const maxLocations = 5;
  const locs = locations ? locations.slice(0, maxLocations) : [];

  // Normalizers across selected locations
  const growthVals = locs.map((l: LocationResult) => Number(l.growth) || 0);
  const growthMin = growthVals.length ? Math.min(...growthVals) : 0;
  const growthMax = growthVals.length ? Math.max(...growthVals) : 1;

  const priceVals = locs.map((l: LocationResult) => l.avgPrice);
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

  // Return raw growth and raw price (affordability) instead of normalized percentages.
  // NOTE: radar scale must adapt to mixed ranges (we compute suggestedMax below).
  const computeRadarFor = (loc: LocationResult) => {
    const transit = Math.round(Math.max(0, Math.min(100, Number(loc.transitScore) || 0)));
    const schools = Math.round(Math.max(0, Math.min(100, Number(loc.schoolScore) || 0)));
    const amenities = Math.round(Math.max(0, Math.min(100, Number(loc.amenitiesScore) || 0)));

    const growthRaw = Number(loc.growth) || 0;
    const affordabilityRaw = Number(loc.avgPrice) / 100 || 0; // CHANGE SCALE DEPENDING ON VALUE OF AFFORDABILITY

    return [transit, schools, amenities, growthRaw, affordabilityRaw];
  };

  const data = {
    labels,
    datasets: locs.map((loc: LocationResult, i: number) => ({
      label: loc.street,
      data: computeRadarFor(loc),
      backgroundColor: paletteBg[i % paletteBg.length],
      borderColor: paletteBorder[i % paletteBorder.length],
      borderWidth: 2,
      pointBackgroundColor: paletteBorder[i % paletteBorder.length],
    })),
  };

  // Debug / validation: log props and generated datasets so you can inspect in devtools
  useEffect(() => {
    console.log('CompareLocations.props.locations:', locations);
    console.log('derived locs:', locs);
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