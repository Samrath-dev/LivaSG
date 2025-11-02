import { HiTrendingUp, HiChartBar, HiFilter } from 'react-icons/hi';
import React, { useRef, useState, useEffect } from 'react';
import api from '../api/https';
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
  facilities: string[];
  description: string;
  amenities: string[];
  transitScore: number;
  schoolScore: number;
  amenitiesScore: number;
}

interface Props {
  locations: LocationResult[];
  onClose: () => void;
}

// Time range options
type TimeRange = '3m' | '6m' | '1y' | '2y' | 'all';

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
  // Errors for radar / price-trend fetches
  const [radarError, setRadarError] = useState<string | null>(null);
  const [priceTrendError, setPriceTrendError] = useState<string | null>(null);
  // simple version keys to trigger retries
  const [breakdownsFetchVersion, setBreakdownsFetchVersion] = useState(0);
  // retry helpers
  const retryFetchBreakdowns = () => {
    setBreakdownsFetchVersion(v => v + 1);
    setRadarError(null);
    setPriceTrendError(null);
    setLoadingPriceTrends(true);
  };

  const [timeRange, setTimeRange] = useState<TimeRange>('all');
  const [showTimeFilter, setShowTimeFilter] = useState(false);

  // Dynamic chart dimensions - INCREASED SIZES
  const [chartDimensions, setChartDimensions] = useState({ 
    width: 900,  // Increased from 800
    height: 500  // Increased from 400
  });
  
  useEffect(() => {
    const updateDimensions = () => {
      const isMobile = window.innerWidth < 768;
      const containerWidth = Math.min(window.innerWidth * 0.85, 900); // Increased from 0.8 to 0.85
      
      if (isMobile) {
        setChartDimensions({
          width: containerWidth,
          height: 420 // Increased from 350
        });
      } else {
        setChartDimensions({
          width: containerWidth,
          height: 450 // Increased from 400
        });
      }
    };

    updateDimensions();
    window.addEventListener('resize', updateDimensions);
    return () => window.removeEventListener('resize', updateDimensions);
  }, []);

  // Filter months based on selected time range
  const filterMonthsByTimeRange = (months: string[]): string[] => {
    if (timeRange === 'all') return months;
    
    const now = new Date();
    let cutoffDate = new Date();
    
    switch (timeRange) {
      case '3m':
        cutoffDate.setMonth(now.getMonth() - 3);
        break;
      case '6m':
        cutoffDate.setMonth(now.getMonth() - 6);
        break;
      case '1y':
        cutoffDate.setFullYear(now.getFullYear() - 1);
        break;
      case '2y':
        cutoffDate.setFullYear(now.getFullYear() - 2);
        break;
    }
    
    return months.filter(month => {
      const monthDate = new Date(month);
      return monthDate >= cutoffDate;
    });
  };

  // total unique months across all fetched priceTrends (used for header badge)
  const totalMonths = React.useMemo(() => {
    const s = new Set<string>();
    Object.values(priceTrends).forEach(arr => {
      if (Array.isArray(arr)) arr.forEach(p => { if (p && p.month) s.add(String(p.month)); });
    });
    return s.size;
  }, [priceTrends]);

  // single-area price trend metrics (mirror DetailsView behavior)
  interface TrendPoint { month: string; median: number; }
  const [metrics, setMetrics] = useState<{
    totalGrowthPercent: number;
    recentGrowthPercent: number;
    trendDirection: 'up' | 'down' | 'stable';
    trendStrength: 'strong' | 'moderate' | 'weak';
    currentPrice: number;
    priceChange: number;
  }>({
    totalGrowthPercent: 0,
    recentGrowthPercent: 0,
    trendDirection: 'stable',
    trendStrength: 'weak',
    currentPrice: 0,
    priceChange: 0,
  });

  const calculateTrendMetrics = (points: TrendPoint[]) => {
    if (!points || points.length < 2) {
      return {
        totalGrowthPercent: 0,
        recentGrowthPercent: 0,
        trendDirection: 'stable' as const,
        trendStrength: 'weak' as const,
        currentPrice: 0,
        priceChange: 0,
      };
    }

    const sorted = [...points].sort((a, b) => new Date(a.month).getTime() - new Date(b.month).getTime());
    const startPrice = sorted[0].median || 0;
    const endPrice = sorted[sorted.length - 1].median || 0;
    const totalGrowthPercent = startPrice ? ((endPrice - startPrice) / startPrice) * 100 : 0;

    const recentPoints = sorted.slice(-Math.min(6, sorted.length));
    const recentStart = recentPoints[0].median || 0;
    const recentEnd = recentPoints[recentPoints.length - 1].median || 0;
    const recentGrowthPercent = recentStart ? ((recentEnd - recentStart) / recentStart) * 100 : 0;

    const lastThree = sorted.slice(-3);
    const prices = lastThree.map(p => p.median || 0);
    const changes = prices.slice(1).map((price, i) => price - prices[i]);
    const avgChange = changes.length ? changes.reduce((s, c) => s + c, 0) / changes.length : 0;

    let trendDirection: 'up' | 'down' | 'stable' = 'stable';
    if (avgChange > 500) trendDirection = 'up';
    else if (avgChange < -500) trendDirection = 'down';

    let trendStrength: 'strong' | 'moderate' | 'weak' = 'weak';
    const priceRange = Math.max(...prices) - Math.min(...prices) || 0;
    if (priceRange > 0) {
      if (Math.abs(avgChange) > priceRange * 0.1) trendStrength = 'strong';
      else if (Math.abs(avgChange) > priceRange * 0.05) trendStrength = 'moderate';
    }

    return {
      totalGrowthPercent,
      recentGrowthPercent,
      trendDirection,
      trendStrength,
      currentPrice: endPrice,
      priceChange: endPrice - startPrice,
    };
  };

  // Fetch single-area price trend for the first selected location and compute metrics
  useEffect(() => {
    let cancelled = false;
    if (!locs.length) return;
    const fetchTrend = async () => {
      try {
        setPriceTrendError(null);
        const area = locs[0].area;
        if (!area) return;
        const areaId = area.replace(/\s+/g, '-');
        const res = await api.get(`/details/${areaId}/price-trend`);
        const raw = (res as any).data;
        const points = Array.isArray(raw?.points) ? raw.points : (Array.isArray(raw) ? raw : []);
        const transformed: TrendPoint[] = points.map((p: any) => ({ month: String(p.month), median: Number(p.median) }));
        if (!cancelled) setMetrics(calculateTrendMetrics(transformed));
      } catch (err: any) {
        console.error('Failed to fetch single-area trend in AnalysisView', err);
        if (!cancelled) setPriceTrendError(`Unable to load price trend: ${err?.message ?? String(err)}`);
      } finally {
      }
    };
    fetchTrend();
    return () => { cancelled = true; };
  }, [locations]);

  // Fetch breakdown scores for each provided location from backend:
  useEffect(() => {
    let cancelled = false;
    if (!locs.length) return;
    (async () => {
      try {
        setRadarError(null);
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
                Object.keys(scores).forEach(k => { normalized[k] = Number(scores[k]); });
                map[loc.id] = normalized;
              } else {
                console.warn('Unexpected breakdown payload for', loc.street, json);
              }
              // fetch price trend for this location (best-effort). Endpoint returns { points: [{month, median}] }
              try {
                const tRes = await fetch(`http://localhost:8000/details/${name}/price-trend`);
                if (tRes.ok) {
                  const tJson = await tRes.json().catch(() => null);
                  const pts = tJson && Array.isArray(tJson.points) ? tJson.points : (Array.isArray(tJson) ? tJson : []);
                  priceMap[loc.id] = pts.map((p: any) => ({ month: String(p.month), median: Number(p.median) }));
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
        }
      } catch (err: any) {
        console.error('Failed to fetch breakdowns/price trends', err);
        if (!cancelled) {
          setRadarError(`Unable to load radar data: ${err?.message ?? String(err)}`);
          setPriceTrendError(`Unable to load price trends: ${err?.message ?? String(err)}`);
        }
      } finally {
        if (!cancelled) setLoadingPriceTrends(false);
      }
    })();
    return () => { cancelled = true; };
  }, [locations, breakdownsFetchVersion]);

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
        
        // map to the new label order: Affordability, Accessibility(transit), Amenities, Environment, Community(schools)
        const affordability = clamp100(Math.round(Math.max(0, Math.min(100, 70)))); // Default moderate score
        const accessibility = clamp100(Math.round((transit / Math.max(1, transit)) * 100)); // best-effort, keeps within 0-100
        const amenitiesScore = clamp100(Math.round(Math.max(0, Math.min(100, amenities))));
        const environment = clamp100(Math.round(Math.max(0, Math.min(100, 80)))); // Default good score
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

    if (priceTrendError) {
      return (
        <div className="flex flex-col items-center justify-center h-48 text-red-600 p-4">
          <div className="text-center">{priceTrendError}</div>
          <button onClick={retryFetchBreakdowns} className="mt-2 px-4 py-2 bg-red-100 text-red-700 rounded-lg">Retry</button>
        </div>
      );
    }

    // gather unique months across all series and sort
    const monthSet = new Set<string>();
    series.forEach(s => s.forEach(p => monthSet.add(p.month)));
    const allMonths = Array.from(monthSet).sort((a, b) => new Date(a).getTime() - new Date(b).getTime());
    
    // Apply time range filter
    const filteredMonths = filterMonthsByTimeRange(allMonths);
    
    if (filteredMonths.length === 0) {
      return (
        <div className="flex items-center justify-center h-48 text-gray-500">
          No price trend data available for the selected time range.
        </div>
      );
    }

    // build lookup for each series by month
    const lookups = series.map(s => {
      const map: Record<string, number> = {};
      s.forEach(p => { map[p.month] = Number(p.median) || 0; });
      return map;
    });

    // compute global min/max using filtered months
    let allValues: number[] = [];
    lookups.forEach(map => filteredMonths.forEach(m => { if (map[m] !== undefined) allValues.push(map[m]); }));
    if (allValues.length === 0) allValues = [0, 1];
    const minV = Math.min(...allValues);
    const maxV = Math.max(...allValues);

    // Layout padding: increased for larger chart
    const isMobile = window.innerWidth < 768;
    const leftPad = isMobile ? 80 : 90;  // Increased padding
    const rightPad = isMobile ? 40 : 60;  // Increased padding
    const topPad = isMobile ? 50 : 60;    // Increased padding
    const bottomPad = isMobile ? 70 : 80; // Increased padding
    
    const { width: chartWidth, height: chartHeight } = chartDimensions;
    const totalHeight = chartHeight + bottomPad;
    const getX = (idx: number) => leftPad + (idx * (chartWidth - leftPad - rightPad) / Math.max(1, filteredMonths.length - 1));
    const getY = (val: number) => chartHeight - bottomPad - ((val - minV) / Math.max(1e-6, (maxV - minV))) * (chartHeight - topPad - bottomPad);

    // build paths using filtered months
    const paths = lookups.map((map, i) => {
      const path = filteredMonths.map((m, idx) => {
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

    const formatPrice = (price: number) => {
      const n = Math.round(Number(price) || 0);
      return `$${n.toLocaleString(undefined)}`;
    };

    // Find January months for yearly vertical grid lines
    const januaryMonths = filteredMonths.reduce((acc: number[], month, idx) => {
      const date = new Date(month);
      if (date.getMonth() === 0) { // January is month 0
        acc.push(idx);
      }
      return acc;
    }, []);

    // determine which month indices should show labels: quarter starts (Jan/Apr/Jul/Oct)
    const quarterIndices = filteredMonths.reduce((acc: number[], m, idx) => {
      const d = new Date(m);
      const mo = isNaN(d.getTime()) ? -1 : d.getMonth();
      if (mo >= 0 && mo % 3 === 0) acc.push(idx);
      return acc;
    }, []);
    const labelIndicesSet = new Set<number>([0, filteredMonths.length - 1, ...quarterIndices]);

    return (
      <div className="bg-white rounded-2xl">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-3 flex-wrap">
            {locs.map((loc, i) => (
              <div key={loc.id} className="flex items-center gap-2 text-sm">
                <span className="w-3 h-3 rounded-sm" style={{ background: paletteBorder[i % paletteBorder.length] }} />
                <span className="text-gray-700 truncate max-w-[120px]">{loc.street}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Time Range Filter */}
        <div className="flex justify-between items-center mb-4">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowTimeFilter(!showTimeFilter)}
              className="flex items-center gap-2 px-3 py-1 text-sm bg-purple-100 text-purple-700 rounded-lg hover:bg-purple-200 transition-colors"
            >
              <HiFilter className="w-4 h-4" />
              <span>Time Range</span>
            </button>
            
            {showTimeFilter && (
              <div className="flex gap-1 bg-white border border-purple-200 rounded-lg p-1 shadow-lg">
                {(['3m', '6m', '1y', '2y', 'all'] as TimeRange[]).map((range) => (
                  <button
                    key={range}
                    onClick={() => {
                      setTimeRange(range);
                      setShowTimeFilter(false);
                    }}
                    className={`px-3 py-1 text-xs rounded-md transition-colors ${
                      timeRange === range
                        ? 'bg-purple-600 text-white'
                        : 'text-purple-600 hover:bg-purple-50'
                    }`}
                  >
                    {range === '3m' ? '3M' : 
                     range === '6m' ? '6M' : 
                     range === '1y' ? '1Y' : 
                     range === '2y' ? '2Y' : 'All'}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Display current time range */}
          <div className="text-sm text-purple-600 font-medium">
            Showing: {timeRange === '3m' ? '3 Months' : 
                     timeRange === '6m' ? '6 Months' : 
                     timeRange === '1y' ? '1 Year' : 
                     timeRange === '2y' ? '2 Years' : 'All Time'}
          </div>
        </div>

        {/* Chart Stats */}
        <div className="flex justify-between items-center mb-4 text-sm">
          <div className="text-green-600 font-semibold">
            +{metrics.totalGrowthPercent.toFixed(1)}% total growth
          </div>
          <div className={`font-semibold ${
            metrics.trendDirection === 'up' ? 'text-green-600' : 
            metrics.trendDirection === 'down' ? 'text-red-600' : 'text-gray-600'
          }`}>
            Trend: {metrics.trendDirection} ({metrics.trendStrength})
          </div>
        </div>

        <div ref={chartContainerRef} className="w-full overflow-hidden relative">
          <svg
            ref={svgRef}
            viewBox={`0 0 ${chartWidth} ${totalHeight}`}
            className="w-full"
            style={{ height: isMobile ? '420px' : '450px' }} // Updated heights
            preserveAspectRatio="xMidYMid meet"
            onMouseMove={(e) => {
              if (!svgRef.current || !chartContainerRef.current) return;
              const svgRect = svgRef.current.getBoundingClientRect();
              const clientX = (e as React.MouseEvent).clientX;
              const relX = clientX - svgRect.left;
              const approx = (relX / svgRect.width) * (filteredMonths.length - 1);
              const idx = Math.max(0, Math.min(filteredMonths.length - 1, Math.round(approx)));
              setHoverIdx(idx);

              // Tooltip placement: prefer to the right of the point, but if
              // that would overflow the svg container, flip to the left.
              const TOOLTIP_MAX_W = 200; // tailwind max-w-[200px]
              const MARGIN = 12;
              const pointPx = (getX(idx) / chartWidth) * svgRect.width;
              // default try to place to the right of point
              let leftCandidate = pointPx + MARGIN;
              // if placing to the right would overflow, place to the left
              if (leftCandidate + TOOLTIP_MAX_W + MARGIN > svgRect.width) {
                leftCandidate = Math.max(MARGIN, pointPx - TOOLTIP_MAX_W - MARGIN);
              }
              // final clamp to container bounds
              const finalLeft = Math.max(MARGIN, Math.min(leftCandidate, Math.max(MARGIN, svgRect.width - MARGIN)));
              setTooltipPos({ left: finalLeft, top: 8 });
            }}
            onMouseLeave={() => { setHoverIdx(null); setTooltipPos(null); }}
            onTouchMove={(e) => {
              if (!svgRef.current || !chartContainerRef.current) return;
              const touch = (e as React.TouchEvent).touches[0];
              if (!touch) return;
              const svgRect = svgRef.current.getBoundingClientRect();
              const relX = touch.clientX - svgRect.left;
              const approx = (relX / svgRect.width) * (filteredMonths.length - 1);
              const idx = Math.max(0, Math.min(filteredMonths.length - 1, Math.round(approx)));
              setHoverIdx(idx);

              const TOOLTIP_MAX_W = 200;
              const MARGIN = 12;
              const pointPx = (getX(idx) / chartWidth) * svgRect.width;
              let leftCandidate = pointPx + MARGIN;
              if (leftCandidate + TOOLTIP_MAX_W + MARGIN > svgRect.width) {
                leftCandidate = Math.max(MARGIN, pointPx - TOOLTIP_MAX_W - MARGIN);
              }
              const finalLeft = Math.max(MARGIN, Math.min(leftCandidate, Math.max(MARGIN, svgRect.width - MARGIN)));
              setTooltipPos({ left: finalLeft, top: 8 });
            }}
            onTouchEnd={() => { setHoverIdx(null); setTooltipPos(null); }}
          >
            {/* Vertical grid lines at January of each year */}
            {januaryMonths.map((idx) => (
              <line 
                key={`vline-${idx}`} 
                x1={getX(idx)} 
                y1={topPad} 
                x2={getX(idx)} 
                y2={chartHeight - bottomPad} 
                stroke="#e5e7eb" 
                strokeWidth="1" 
                strokeDasharray="4 2"
              />
            ))}

            {/* Horizontal grid lines every 100k */}
            {(() => {
              const lines: React.ReactNode[] = [];
              const step = 100000;
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
              filteredMonths.map((m, mi) => {
                const v = map[m];
                if (v === undefined) return null;
                return (
                  <circle key={`${si}-${mi}`} cx={getX(mi)} cy={getY(v)} r={isMobile ? 2 : 3} fill={paletteBorder[si % paletteBorder.length]} />
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
                  const m = filteredMonths[hoverIdx];
                  const v = map[m];
                  if (v === undefined) return null;
                  return (
                    <circle key={`h-${si}`} cx={getX(hoverIdx)} cy={getY(v)} r={isMobile ? 4 : 6} fill="#fff" stroke={paletteBorder[si % paletteBorder.length]} strokeWidth={2} />
                  );
                })}
              </g>
            )}

            {/* axes */}
            <line x1={leftPad} y1={topPad} x2={leftPad} y2={chartHeight - bottomPad} stroke="#6b7280" strokeWidth="1" />
            <line x1={leftPad} y1={chartHeight - bottomPad} x2={chartWidth - rightPad} y2={chartHeight - bottomPad} stroke="#6b7280" strokeWidth="1" />

            {/* left-side labels */}
            <text
              x={leftPad - 12}
              y={topPad}
              textAnchor="end"
              dominantBaseline="middle"
              style={{ fontSize: isMobile ? '10px' : '12px', fontFamily: 'Inter, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial', fill: '#6b7280' }}
            >
              {formatPrice(maxV)}
            </text>
            <text
              x={leftPad - 12}
              y={(chartHeight / 2)}
              textAnchor="end"
              dominantBaseline="middle"
              style={{ fontSize: isMobile ? '10px' : '12px', fontFamily: 'Inter, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial', fill: '#6b7280' }}
            >
              {formatPrice((maxV + minV) / 2)}
            </text>
            <text
              x={leftPad - 12}
              y={chartHeight - bottomPad}
              textAnchor="end"
              dominantBaseline="middle"
              style={{ fontSize: isMobile ? '10px' : '12px', fontFamily: 'Inter, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial', fill: '#6b7280' }}
            >
              {formatPrice(minV)}
            </text>

            {/* month labels: only quarter starts (Jan/Apr/Jul/Oct) plus first & last */}
            {filteredMonths.map((m, idx) => {
              if (!labelIndicesSet.has(idx)) return null;
              const x = getX(idx);
              const y = chartHeight - bottomPad + (isMobile ? 24 : 28);
              return (
                <text
                  key={`lbl-${m}-${idx}`}
                  x={x}
                  y={y}
                  transform={`rotate(-45 ${x} ${y})`}
                  textAnchor="end"
                  style={{ 
                    fontSize: isMobile ? '10px' : '12px', 
                    fontFamily: 'Inter, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial', 
                    fill: '#6b7280' 
                  }}
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
              className="absolute z-50 pointer-events-none w-max bg-white border border-gray-200 rounded-md shadow-lg p-2 text-xs max-w-[200px]"
            >
              <div className="font-semibold text-gray-800 mb-1">{formatDateLabel(filteredMonths[hoverIdx])}</div>
              <div className="space-y-1">
                {locs.map((loc, i) => {
                  const val = lookups[i][filteredMonths[hoverIdx]];
                  return (
                    <div key={`t-${loc.id}`} className="flex items-center gap-2">
                      <span style={{ width: 8, height: 8, background: paletteBorder[i % paletteBorder.length] }} className="inline-block rounded-sm" />
                      <span className="text-gray-700 truncate">{loc.street}:</span>
                      <span className="font-semibold text-gray-900 whitespace-nowrap">{val !== undefined ? formatPrice(val) : '—'}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* Data summary: recent growth and current median shown side-by-side */}
        <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className={`flex flex-col items-center justify-center p-4 rounded-lg ${metrics.recentGrowthPercent < 0 ? 'bg-red-50' : metrics.recentGrowthPercent > 0 ? 'bg-green-50' : 'bg-gray-50'}`}>
            <div className="text-sm text-gray-600">Recent Growth</div>
            <div className={`${metrics.recentGrowthPercent < 0 ? 'text-red-600' : metrics.recentGrowthPercent > 0 ? 'text-green-600' : 'text-gray-700'} font-semibold text-lg`}>
              {metrics.recentGrowthPercent > 0 ? '+' : ''}{metrics.recentGrowthPercent.toFixed(1)}%
            </div>
          </div>

          <div className="flex flex-col items-center justify-center p-4 bg-purple-50 rounded-lg">
            <div className="text-sm text-gray-600">Current Median</div>
            <div className="text-purple-700 font-semibold text-lg">
              {formatPrice(metrics.currentPrice)}
            </div>
          </div>
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
      typeof l.amenitiesScore !== 'number'
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
        pointLabels: { color: '#6b21a8', font: { size: 14 }, padding: 18 }, // Increased font size and padding
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
          {/* Radar attributes box — increased size */}
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-purple-200 w-full">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-bold text-lg text-purple-900 flex items-center gap-2">
                <span className="inline-flex items-center justify-center w-6 h-6 rounded-md bg-purple-100 text-purple-700">
                  <HiChartBar className="w-4 h-4" />
                </span>
                Radar Chart
              </h2>
              <div className="text-sm text-purple-600 font-medium bg-purple-100 px-3 py-1 rounded-full">
                {locs.length == 1 ? '1 location' : `${locs.length} locations`}
              </div>
            </div>

            {/* Increased radar chart size */}
            <div className="relative overflow-visible mx-auto" style={{ 
              maxHeight: 'min(80vh, 95vw)', // Increased from 70vh, 90vw
              aspectRatio: '1 / 1',
              width: '100%'
            }}>
              {radarError ? (
                <div className="flex flex-col items-center justify-center h-64 text-red-600 p-4">
                  <div className="text-center mb-2">{radarError}</div>
                  <button onClick={retryFetchBreakdowns} className="mt-2 px-4 py-2 bg-red-100 text-red-700 rounded-lg">Retry</button>
                </div>
              ) : (
                <div className="absolute inset-0 flex items-center justify-center p-2">
                  <div className="w-full h-full">
                    <Radar
                      data={data}
                      options={{ ...options, responsive: true, maintainAspectRatio: false }}
                      style={{ width: '100%', height: '100%' }}
                    />
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Price History with Time Range Filter */}
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-purple-200 mt-4 w-full">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-bold text-lg text-purple-900 flex items-center gap-2">
                <HiTrendingUp className="w-5 h-5 text-purple-500" />
                Price Trend
              </h2>
              <div className="text-sm text-purple-600 font-medium bg-purple-100 px-3 py-1 rounded-full">
                {filterMonthsByTimeRange(
                  Array.from(
                    new Set(
                      Object.values(priceTrends).flatMap(arr => 
                        arr.map(p => p.month)
                      )
                    )
                  )
                ).length} months
              </div>
            </div>
            {renderPriceComparisonChart()}
          </div>
        </div>
      </div>
    </div>
  );
}