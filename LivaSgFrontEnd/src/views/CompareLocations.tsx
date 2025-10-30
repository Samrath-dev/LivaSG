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
  // round and format with thousands separator, keep dollar sign
  const n = Math.round(Number(price) || 0);
  return `$${n.toLocaleString(undefined)}`;
};

export default function CompareLocations({ locations, onClose }: Props) {
  const labels = ['Affordability', 'Accessibility', 'Amenities', 'Environment', 'Community'];

  // limit to up to 5 locations
  const maxLocations = 5;
  const locs = locations ? locations.slice(0, maxLocations) : [];

  // fetched breakdowns keyed by location id
  const [breakdowns, setBreakdowns] = useState<Record<number, Record<string, number>>>({});
  // fetched price trends keyed by location id
  const [priceTrends, setPriceTrends] = useState<Record<number, Array<{ month: string; median: number }>>>({});
  const [loadingPriceTrends, setLoadingPriceTrends] = useState(false);

  // Fetch breakdown scores for each provided location from backend:
  useEffect(() => {
    let cancelled = false;
    if (!locs.length) return;
    (async () => {
      const map: Record<number, Record<string, number>> = {};
      const priceMap: Record<number, Array<{ month: string; median: number }>> = {};
      setLoadingPriceTrends(true);
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
            // fetch price trend for this location (best-effort). Endpoint returns { points: [{month, median}] }
            try {
              const tRes = await fetch(`http://localhost:8000/details/${name}/price-trend`);
              if (tRes.ok) {
                const tJson = await tRes.json().catch(() => null);
                const points = Array.isArray(tJson?.points) ? tJson.points : (Array.isArray(tJson) ? tJson : null);
                if (points && Array.isArray(points)) {
                  priceMap[loc.id] = points.map((p: any) => ({ month: String(p.month), median: Number(p.median) }));
                }
              }
            } catch (tErr) {
              // ignore trend fetch errors for individual locations
            }
          } catch (err) {
            console.warn('Failed to fetch breakdown for', loc.street, err);
          }
        })
      );
      if (!cancelled) {
        setBreakdowns(map);
        setPriceTrends(priceMap);
        setLoadingPriceTrends(false);
      }
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

  // Render combined price trend chart for selected locations
  const renderPriceComparisonChart = () => {
    // if no trends yet, show placeholder
    const ids = locs.map(l => l.id);
    const series = ids.map(id => priceTrends[id] || []);
    const anyLoaded = series.some(s => s && s.length > 0);
    if (loadingPriceTrends && !anyLoaded) {
      return (
        <div className="flex items-center justify-center h-48">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500"></div>
          <span className="ml-3 text-purple-600">Loading comparison trends...</span>
        </div>
      );
    }

    // gather unique months across all series and sort
    const monthSet = new Set<string>();
    series.forEach(s => s.forEach(p => monthSet.add(p.month)));
    const months = Array.from(monthSet).sort((a, b) => new Date(a).getTime() - new Date(b).getTime());
    if (months.length === 0) {
      return (
        <div className="flex items-center justify-center h-48 text-gray-500">No price trend data available for selected locations.</div>
      );
    }

    // build lookup for each series by month
    const lookups = series.map(s => {
      const map: Record<string, number> = {};
      s.forEach(p => { map[p.month] = Number(p.median) || 0; });
      return map;
    });

    // compute global min/max
    let allValues: number[] = [];
    lookups.forEach(map => months.forEach(m => { if (map[m] !== undefined) allValues.push(map[m]); }));
    if (allValues.length === 0) allValues = [0, 1];
    const minV = Math.min(...allValues);
    const maxV = Math.max(...allValues);
  // Layout padding: separate left/right/top/bottom so labels are not clipped
  const leftPad = 72;
  const rightPad = 48;
  const topPad = 48;
  const bottomPad = 60; // room for rotated x labels
  const chartWidth = 800;
  const chartHeight = 400; // plot height
  const totalHeight = chartHeight + bottomPad;
    const getX = (idx: number) => leftPad + (idx * (chartWidth - leftPad - rightPad) / Math.max(1, months.length - 1));
    const getY = (val: number) => chartHeight - bottomPad - ((val - minV) / Math.max(1e-6, (maxV - minV))) * (chartHeight - topPad - bottomPad);

    // build paths
    const paths = lookups.map((map, i) => {
      const path = months.map((m, idx) => {
        const v = map[m] !== undefined ? map[m] : null;
        const x = getX(idx);
        const y = v !== null ? getY(v) : getY(minV);
        return `${idx === 0 ? 'M' : 'L'} ${x} ${y}`;
      }).join(' ');
      return { path, color: paletteBorder[i % paletteBorder.length] };
    });

    const formatDateLabel = (d: string) => {
      const date = new Date(d);
      if (isNaN(date.getTime())) return d;
      return date.toLocaleDateString(undefined, { month: 'short', year: 'numeric' });
    };

  // determine which month indices should show labels: quarter starts (Jan/Apr/Jul/Oct)
  // Always include first and last index for context.
  const quarterIndices = months.reduce((acc: number[], m, idx) => {
    const d = new Date(m);
    const mo = isNaN(d.getTime()) ? -1 : d.getMonth();
    if (mo >= 0 && mo % 3 === 0) acc.push(idx);
    return acc;
  }, []);
  const labelIndicesSet = new Set<number>([0, months.length - 1, ...quarterIndices]);

    return (
      <div className="bg-white rounded-2xl p-4 border border-purple-100">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-md font-semibold text-purple-900">Price Trends Comparison</h3>
          <div className="flex items-center gap-3">
            {locs.map((loc, i) => (
              <div key={loc.id} className="flex items-center gap-2 text-sm">
                <span className="w-3 h-3 rounded-sm" style={{ background: paletteBorder[i % paletteBorder.length] }} />
                <span className="text-gray-700">{loc.street}</span>
              </div>
            ))}
          </div>
        </div>
        <div ref={chartContainerRef} className="w-full overflow-hidden relative">
          <svg
            ref={svgRef}
            viewBox={`0 0 ${chartWidth} ${totalHeight}`}
            className="w-full h-[400px]"
            preserveAspectRatio="none"
            onMouseMove={(e) => {
              if (!svgRef.current || !chartContainerRef.current) return;
              const svgRect = svgRef.current.getBoundingClientRect();
              const clientX = (e as React.MouseEvent).clientX;
              const relX = clientX - svgRect.left;
              const approx = (relX / svgRect.width) * (months.length - 1);
              const idx = Math.max(0, Math.min(months.length - 1, Math.round(approx)));
              setHoverIdx(idx);
              // position tooltip near top of chart at the hovered x (relative to container)
              const leftPx = (getX(idx) / chartWidth) * svgRect.width;
              setTooltipPos({ left: leftPx, top: 8 });
            }}
            onMouseLeave={() => { setHoverIdx(null); setTooltipPos(null); }}
            onTouchMove={(e) => {
              if (!svgRef.current || !chartContainerRef.current) return;
              const touch = (e as React.TouchEvent).touches[0];
              if (!touch) return;
              const svgRect = svgRef.current.getBoundingClientRect();
              const relX = touch.clientX - svgRect.left;
              const approx = (relX / svgRect.width) * (months.length - 1);
              const idx = Math.max(0, Math.min(months.length - 1, Math.round(approx)));
              setHoverIdx(idx);
              const leftPx = (getX(idx) / chartWidth) * svgRect.width;
              setTooltipPos({ left: leftPx, top: 8 });
            }}
            onTouchEnd={() => { setHoverIdx(null); setTooltipPos(null); }}
          >
            {/* horizontal grid lines every 100k */}
            {(() => {
              const lines: React.ReactNode[] = [];
              const step = 100000;
              // find first tick >= minV that is aligned to step
              const startTick = Math.ceil(minV / step) * step;
              const endTick = Math.floor(maxV / step) * step;
              if (startTick <= endTick) {
                for (let v = startTick; v <= endTick; v += step) {
                  const y = getY(v);
                  lines.push(
                    <line key={`tick-${v}`} x1={leftPad} y1={y} x2={chartWidth - rightPad} y2={y} stroke="#e5e7eb" strokeWidth="1" />
                  );
                }
              }
              return lines;
            })()}

            {/* series paths */}
            {paths.map((p, i) => (
              <path key={i} d={p.path} fill="none" stroke={p.color} strokeWidth={2.5} strokeLinecap="round" strokeLinejoin="round" />
            ))}

            {/* data markers */}
            {lookups.map((map, si) => (
              months.map((m, mi) => {
                const v = map[m];
                if (v === undefined) return null;
                return (
                  <circle key={`${si}-${mi}`} cx={getX(mi)} cy={getY(v)} r={3} fill={paletteBorder[si % paletteBorder.length]} />
                );
              })
            ))}

            {/* hover vertical line & highlights */}
            {hoverIdx !== null && (
              <g>
                <line
                  x1={getX(hoverIdx)}
                  x2={getX(hoverIdx)}
                  y1={topPad}
                  y2={chartHeight - bottomPad}
                  stroke="#9CA3AF"
                  strokeWidth={1}
                  strokeDasharray="4 4"
                />
                {lookups.map((map, si) => {
                  const m = months[hoverIdx];
                  const v = map[m];
                  if (v === undefined) return null;
                  return (
                    <circle key={`h-${si}`} cx={getX(hoverIdx)} cy={getY(v)} r={6} fill="#fff" stroke={paletteBorder[si % paletteBorder.length]} strokeWidth={2} />
                  );
                })}
              </g>
            )}

            {/* axes */}
            <line x1={leftPad} y1={topPad} x2={leftPad} y2={chartHeight - bottomPad} stroke="#6b7280" strokeWidth="1" />
            <line x1={leftPad} y1={chartHeight - bottomPad} x2={chartWidth - rightPad} y2={chartHeight - bottomPad} stroke="#6b7280" strokeWidth="1" />

            {/* left-side labels: top / middle / bottom values (formatted) */}
            <text
              x={leftPad - 12}
              y={topPad}
              textAnchor="end"
              dominantBaseline="middle"
              style={{ fontSize: '12px', fontFamily: 'Inter, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial', fill: '#6b7280' }}
            >
              {formatPrice(maxV)}
            </text>
            <text
              x={leftPad - 12}
              y={(chartHeight / 2)}
              textAnchor="end"
              dominantBaseline="middle"
              style={{ fontSize: '12px', fontFamily: 'Inter, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial', fill: '#6b7280' }}
            >
              {formatPrice((maxV + minV) / 2)}
            </text>
            <text
              x={leftPad - 12}
              y={chartHeight - bottomPad}
              textAnchor="end"
              dominantBaseline="middle"
              style={{ fontSize: '12px', fontFamily: 'Inter, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial', fill: '#6b7280' }}
            >
              {formatPrice(minV)}
            </text>

            {/* soft vertical lines marking start of year (January) */}
            {months.map((m, idx) => {
              const d = new Date(m);
              if (isNaN(d.getTime())) return null;
              if (d.getMonth() === 0) {
                return (
                  <line key={`yr-${idx}`} x1={getX(idx)} x2={getX(idx)} y1={topPad} y2={chartHeight - bottomPad} stroke="#e5e7eb" strokeWidth={1} />
                );
              }
              return null;
            })}

            {/* month labels: only quarter starts (Jan/Apr/Jul/Oct) plus first & last */}
            {months.map((m, idx) => {
              if (!labelIndicesSet.has(idx)) return null;
              const x = getX(idx);
              const y = chartHeight - bottomPad + 28;
              // rotate labels slightly for readability (less steep)
              return (
                <text
                  key={`lbl-${m}-${idx}`}
                  x={x}
                  y={y}
                  transform={`rotate(-45 ${x} ${y})`}
                  textAnchor="end"
                  style={{ fontSize: '12px', fontFamily: 'Inter, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial', fill: '#6b7280' }}
                >
                  {formatDateLabel(m)}
                </text>
              );
            })}
          </svg>

          {/* Tooltip (HTML) positioned over the svg */}
          {tooltipPos && hoverIdx !== null && (
            <div
              style={{ left: tooltipPos.left, top: tooltipPos.top }}
              className="absolute z-50 pointer-events-none w-max bg-white border border-gray-200 rounded-md shadow-lg p-2 text-xs"
            >
              <div className="font-semibold text-gray-800 mb-1">{formatDateLabel(months[hoverIdx])}</div>
              <div className="space-y-1">
                {locs.map((loc, i) => {
                  const val = lookups[i][months[hoverIdx]];
                  return (
                    <div key={`t-${loc.id}`} className="flex items-center gap-2">
                      <span style={{ width: 10, height: 10, background: paletteBorder[i % paletteBorder.length] }} className="inline-block rounded-sm" />
                      <span className="text-gray-700">{loc.street}:</span>
                      <span className="font-semibold text-gray-900">{val !== undefined ? formatPrice(val) : '—'}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>
    );
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

  // chart interactivity refs/state for price comparison
  const chartContainerRef = useRef<HTMLDivElement | null>(null);
  const svgRef = useRef<SVGSVGElement | null>(null);
  const [hoverIdx, setHoverIdx] = useState<number | null>(null);
  const [tooltipPos, setTooltipPos] = useState<{ left: number; top: number } | null>(null);

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

          {/* Price comparison chart for selected locations */}
          <div className="mt-4">
            {renderPriceComparisonChart()}
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