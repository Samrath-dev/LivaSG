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
  location1: LocationResult;
  location2: LocationResult;
  onClose: () => void;
}

const computeRadarScores = (locA: LocationResult, locB: LocationResult) => {
  const growthMax = Math.max(Math.abs(locA.growth), Math.abs(locB.growth), 1);
  const priceMax = Math.max(locA.avgPrice, locB.avgPrice, 1);

  const transit = Math.round(locA.transitScore);
  const schools = Math.round(locA.schoolScore);
  const amenities = Math.round(locA.amenitiesScore);
  const growth = Math.round((Math.abs(locA.growth) / growthMax) * 100);
  const affordability = Math.round(((priceMax - locA.avgPrice) / priceMax) * 100);

  return [transit, schools, amenities, growth, affordability];
};

const formatPrice = (price: number) => {
  if (price >= 1000000) {
    return `$${(price / 1000000).toFixed(1)}M`;
  }
  return `$${(price / 1000).toFixed(0)}K`;
};

export default function CompareLocations({ location1, location2, onClose }: Props) {
  const labels = ['Transit', 'Schools', 'Amenities', 'Growth', 'Affordability'];

  const data = {
    labels,
    datasets: [
      {
        label: location1.street,
        data: computeRadarScores(location1, location2),
        backgroundColor: 'rgba(99,102,241,0.2)',
        borderColor: 'rgba(99,102,241,1)',
        borderWidth: 2,
        pointBackgroundColor: 'rgba(99,102,241,1)',
      },
      {
        label: location2.street,
        data: computeRadarScores(location2, location1),
        backgroundColor: 'rgba(16,185,129,0.15)',
        borderColor: 'rgba(16,185,129,1)',
        borderWidth: 2,
        pointBackgroundColor: 'rgba(16,185,129,1)',
      },
    ],
  };

  const options = {
    scales: {
      r: {
        suggestedMin: 0,
        suggestedMax: 100,
        ticks: { stepSize: 20, color: '#6b21a8' },
        pointLabels: { color: '#6b21a8', font: { size: 12 } },
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
            className="bg-purple-50 p-4 rounded-xl w-full max-w-full mx-auto relative overflow-hidden flex-none"
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

          {/* Summary cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
            {[location1, location2].map((loc) => (
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