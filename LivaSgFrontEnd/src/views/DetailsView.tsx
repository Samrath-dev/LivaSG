import { HiChevronLeft, HiTrendingUp, HiStar, HiMap, HiHome, HiInformationCircle } from 'react-icons/hi';
import { useState, useEffect } from 'react';
import { FaDumbbell, FaTree, FaShoppingBag, FaSchool, FaHospital, FaParking, FaUtensils } from 'react-icons/fa';
import React, { isValidElement, cloneElement } from 'react';
import type { ReactNode } from 'react';
import OneMapEmbedded from '../components/OneMapEmbedded';
import api from '../api/https';

interface DetailsViewProps {
  location: {
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
    latitude?: number;
    longitude?: number;
    lat?: number;
    lng?: number;
  };
  onBack: () => void;
}

type FilterItemProps = {
  icon: ReactNode;
  label: string;
  checked: boolean;
  onChange: () => void;
  count?: number;
  iconStyle?: React.CSSProperties;
  iconClassName?: string;
};

// Updated interface to match your API response
interface PriceTrendResponse {
  areaId: string;
  points: Array<{
    month: string;
    median: number;
  }>;
}

// Internal interface for processed data
interface PricePoint {
  month: string;
  medianResale: number;
}

const DetailsView = ({ location, onBack }: DetailsViewProps) => {
  const formatPrice = (price: number) => {
    if (price >= 1000000) {
      return `$${(price / 1000000).toFixed(1)}M`;
    }
    return `$${(price / 1000).toFixed(0)}K`;
  };

  // Get coordinates from location, with fallback to Singapore center
  const getLocationCoordinates = (): [number, number] => {
    if (location.latitude !== undefined && location.longitude !== undefined) {
      return [location.latitude, location.longitude];
    }
    if (location.lat !== undefined && location.lng !== undefined) {
      return [location.lat, location.lng];
    }
    return [1.3521, 103.8198];
  };

  const mapCenter = getLocationCoordinates();

  const [showFilterMenu, setShowFilterMenu] = useState(false);
  const [facilityMarkers, setFacilityMarkers] = useState<Array<{
    position: [number, number];
    popup: string;
  }>>([]);
  const [loadingFacilities, setLoadingFacilities] = useState(false);
  const [facilityCounts, setFacilityCounts] = useState<{
    gym: number;
    park: number;
    mall: number;
    school: number;
    hospital: number;
    parking: number;
    dining: number;
  }>({
    gym: 0,
    park: 0,
    mall: 0,
    school: 0,
    hospital: 0,
    parking: 0,
    dining: 0
  });
  const [selectedOptions, setSelectedOptions] = useState<{ 
    gym: boolean; 
    park: boolean;
    mall: boolean;
    school: boolean;
    hospital: boolean;
    parking: boolean;
    dining: boolean;
  }>({
    gym: false,
    park: false,
    mall: false,
    school: false,
    hospital: false,
    parking: false,
    dining: false
  });

  // Price trend state - updated to match new API structure
  const [priceTrend, setPriceTrend] = useState<PricePoint[] | null>(null);
  const [loadingTrend, setLoadingTrend] = useState(false);
  const [trendError, setTrendError] = useState<string | null>(null);

  // Calculate trend metrics from the data
  const calculateTrendMetrics = (points: PricePoint[]) => {
    if (points.length < 2) {
      return {
        totalGrowthPercent: 0,
        recentGrowthPercent: 0,
        trendDirection: 'stable',
        trendStrength: 'weak',
        currentPrice: 0,
        priceChange: 0
      };
    }

    const sortedPoints = points.sort((a, b) => new Date(a.month).getTime() - new Date(b.month).getTime());
    const startPrice = sortedPoints[0].medianResale;
    const endPrice = sortedPoints[sortedPoints.length - 1].medianResale;
    const totalGrowthPercent = ((endPrice - startPrice) / startPrice) * 100;

    // Calculate recent growth (last 6 months or available data)
    const recentPoints = sortedPoints.slice(-Math.min(6, sortedPoints.length));
    const recentStartPrice = recentPoints[0].medianResale;
    const recentEndPrice = recentPoints[recentPoints.length - 1].medianResale;
    const recentGrowthPercent = ((recentEndPrice - recentStartPrice) / recentStartPrice) * 100;

    // Calculate trend direction based on last 3 points
    const lastThreePoints = sortedPoints.slice(-3);
    const prices = lastThreePoints.map(p => p.medianResale);
    const changes = prices.slice(1).map((price, i) => price - prices[i]);
    const avgChange = changes.reduce((sum, change) => sum + change, 0) / changes.length;
    
    let trendDirection: 'up' | 'down' | 'stable' = 'stable';
    if (avgChange > 500) trendDirection = 'up';
    else if (avgChange < -500) trendDirection = 'down';

    let trendStrength: 'strong' | 'moderate' | 'weak' = 'weak';
    const priceRange = Math.max(...prices) - Math.min(...prices);
    if (Math.abs(avgChange) > priceRange * 0.1) trendStrength = 'strong';
    else if (Math.abs(avgChange) > priceRange * 0.05) trendStrength = 'moderate';

    return {
      totalGrowthPercent,
      recentGrowthPercent,
      trendDirection,
      trendStrength,
      currentPrice: endPrice,
      priceChange: endPrice - startPrice
    };
  };

  // Fetch price trend data - updated to handle new API format
  useEffect(() => {
    const fetchPriceTrend = async () => {
      setLoadingTrend(true);
      setTrendError(null);
      try {
        // Use area name as areaId - replace spaces with hyphens for URL
        const areaId = location.area.replace(/\s+/g, '-');
        
        console.log('Fetching price trend for area:', areaId);
        const response = await api.get<PriceTrendResponse>(`/details/${areaId}/price-trend`);
        console.log('Price trend response:', response.data);
        
        // Transform the data to match the expected format
        const transformedData: PricePoint[] = response.data.points.map(point => ({
          month: point.month,
          medianResale: point.median
        }));
        
        setPriceTrend(transformedData);
      } catch (error: any) {
        console.error('Failed to fetch price trend:', error);
        setTrendError(`Unable to load price trend data: ${error.response?.data?.detail || error.message}`);
      } finally {
        setLoadingTrend(false);
      }
    };

    fetchPriceTrend();
  }, [location.area]);

  // Render price trend chart
  const renderPriceChart = () => {
    if (loadingTrend) {
      return (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500"></div>
          <span className="ml-3 text-purple-600">Loading price trend...</span>
        </div>
      );
    }

    if (trendError) {
      return (
        <div className="flex flex-col items-center justify-center h-64 text-red-600 p-4">
          <span className="text-center">{trendError}</span>
          <button 
            onClick={() => window.location.reload()}
            className="mt-2 px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors"
          >
            Retry
          </button>
        </div>
      );
    }

    if (!priceTrend || priceTrend.length === 0) {
      return (
        <div className="flex items-center justify-center h-64 text-gray-500">
          <span>No price trend data available for {location.area}</span>
        </div>
      );
    }

    const points = priceTrend;
    const metrics = calculateTrendMetrics(points);
    const maxPrice = Math.max(...points.map(p => p.medianResale));
    const minPrice = Math.min(...points.map(p => p.medianResale));
    const priceRange = maxPrice - minPrice || 1;
    
    // Simple SVG line chart
    const chartHeight = 200;
    const chartWidth = 400;
    const padding = 40;

    const getX = (index: number) => padding + (index * (chartWidth - 2 * padding) / (points.length - 1));
    const getY = (price: number) => chartHeight - padding - ((price - minPrice) / priceRange) * (chartHeight - 2 * padding);

    const pathData = points.map((point, index) => 
      `${index === 0 ? 'M' : 'L'} ${getX(index)} ${getY(point.medianResale)}`
    ).join(' ');

    // Format date for display
    const formatDate = (dateString: string) => {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short' });
    };

    return (
      <div className="w-full">
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

        {/* SVG Chart */}
        <div className="w-full overflow-hidden">
          <svg 
            viewBox={`0 0 ${chartWidth} ${chartHeight}`} 
            className="w-full h-48"
            preserveAspectRatio="none"
          >
            {/* Grid lines */}
            <line x1={padding} y1={padding} x2={chartWidth - padding} y2={padding} stroke="#e5e7eb" strokeWidth="1" />
            <line x1={padding} y1={chartHeight / 2} x2={chartWidth - padding} y2={chartHeight / 2} stroke="#e5e7eb" strokeWidth="1" />
            <line x1={padding} y1={chartHeight - padding} x2={chartWidth - padding} y2={chartHeight - padding} stroke="#e5e7eb" strokeWidth="1" />
            
            {/* Price line */}
            <path 
              d={pathData} 
              fill="none" 
              stroke={metrics.trendDirection === 'up' ? '#10b981' : '#ef4444'} 
              strokeWidth="3"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            
            {/* Data points */}
            {points.map((point, index) => (
              <circle 
                key={index}
                cx={getX(index)} 
                cy={getY(point.medianResale)} 
                r="3" 
                fill={metrics.trendDirection === 'up' ? '#10b981' : '#ef4444'}
                className="hover:r-4 transition-all"
              />
            ))}
            
            {/* Axes */}
            <line x1={padding} y1={padding} x2={padding} y2={chartHeight - padding} stroke="#6b7280" strokeWidth="2" />
            <line x1={padding} y1={chartHeight - padding} x2={chartWidth - padding} y2={chartHeight - padding} stroke="#6b7280" strokeWidth="2" />
            
            {/* Labels */}
            <text x={padding - 10} y={padding} textAnchor="end" dominantBaseline="middle" className="text-xs fill-gray-600">
              {formatPrice(maxPrice)}
            </text>
            <text x={padding - 10} y={chartHeight / 2} textAnchor="end" dominantBaseline="middle" className="text-xs fill-gray-600">
              {formatPrice((maxPrice + minPrice) / 2)}
            </text>
            <text x={padding - 10} y={chartHeight - padding} textAnchor="end" dominantBaseline="middle" className="text-xs fill-gray-600">
              {formatPrice(minPrice)}
            </text>
          </svg>
        </div>

        {/* Timeline labels */}
        <div className="flex justify-between text-xs text-gray-500 mt-2 px-4">
          <span>{points[0]?.month ? formatDate(points[0].month) : 'Start'}</span>
          <span>{points[points.length - 1]?.month ? formatDate(points[points.length - 1].month) : 'Present'}</span>
        </div>

        {/* Data summary - REMOVED: Time frame blue box, kept only recent growth */}
        <div className="mt-4 text-center p-2 bg-green-50 rounded-lg">
          <div className="text-green-600 font-semibold">
            {metrics.recentGrowthPercent > 0 ? '+' : ''}{metrics.recentGrowthPercent.toFixed(1)}%
          </div>
          <div className="text-green-800">Recent Growth</div>
        </div>

        {/* Current Price */}
        <div className="mt-4 text-center p-3 bg-purple-50 rounded-lg">
          <div className="text-purple-700 font-semibold">
            Current Median: {formatPrice(metrics.currentPrice)}
          </div>
        </div>
      </div>
    );
  };

  const toggleOption = (key: keyof typeof selectedOptions) => {
    setSelectedOptions(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const fetchFacilities = async () => {
    if (!location.street) return;
    
    setLoadingFacilities(true);
    try {
      // Map UI filter keys to backend types
      const filterMap: Record<string, string> = {
        gym: 'sports',
        park: 'parks',
        mall: 'sports',
        school: 'schools',
        hospital: 'healthcare',
        parking: 'carparks',
        dining: 'hawkers'
      };

      // Get selected types
      const selectedTypes = Object.entries(selectedOptions)
        .filter(([_, checked]) => checked)
        .map(([key, _]) => filterMap[key])
        .filter((v, i, a) => a.indexOf(v) === i) // remove duplicates
        .join(',');

      if (!selectedTypes) {
        setFacilityMarkers([]);
        return;
      }

      const response = await api.get(
        `/details/street/${encodeURIComponent(location.street)}/facilities-locations`,
        { params: { types: selectedTypes } }
      );

      const data = response.data as {
        facilities: Record<string, Array<{ name: string; latitude: number; longitude: number; distance: number }>>;
      };
      const markers: Array<{ position: [number, number]; popup: string }> = [];

      // Convert facilities to markers
      const categoryIcons: Record<string, string> = {
        schools: '🏫',
        sports: '⚽',
        hawkers: '🍽️',
        healthcare: '🏥',
        parks: '🌳',
        carparks: '🅿️'
      };

      Object.entries(data.facilities).forEach(([category, items]: [string, any]) => {
        if (Array.isArray(items)) {
          items.forEach((facility: any) => {
            markers.push({
              position: [facility.latitude, facility.longitude],
              popup: `${categoryIcons[category] || '📍'} <strong>${facility.name}</strong><br/>${category}<br/>${facility.distance}km away`
            });
          });
        }
      });

      setFacilityMarkers(markers);
    } catch (error) {
      console.error('Failed to fetch facilities:', error);
      setFacilityMarkers([]);
    } finally {
      setLoadingFacilities(false);
    }
  };

  // Fetch facility counts on mount
  useEffect(() => {
    const fetchFacilityCounts = async () => {
      if (!location.street) return;
      
      try {
        // Fetch all facilities to get counts
        const response = await api.get(
          `/details/street/${encodeURIComponent(location.street)}/facilities-locations`,
          { params: { types: 'schools,sports,hawkers,healthcare,parks,carparks' } }
        );

        const data = response.data as {
          facilities: Record<string, Array<any>>;
        };

        // Map backend categories to UI keys
        const counts = {
          gym: data.facilities.sports?.length || 0,
          park: data.facilities.parks?.length || 0,
          mall: data.facilities.sports?.length || 0, // mall uses sports
          school: data.facilities.schools?.length || 0,
          hospital: data.facilities.healthcare?.length || 0,
          parking: data.facilities.carparks?.length || 0,
          dining: data.facilities.hawkers?.length || 0
        };

        setFacilityCounts(counts);
      } catch (error) {
        console.error('Failed to fetch facility counts:', error);
      }
    };

    fetchFacilityCounts();
  }, [location.street]);

  const handleApplyFilters = async () => {
    await fetchFacilities();
    setShowFilterMenu(false);
  };

  const handleResetFilters = () => {
    setSelectedOptions({
      gym: false,
      park: false,
      mall: false,
      school: false,
      hospital: false,
      parking: false,
      dining: false
    });
    setFacilityMarkers([]);
  };

  const FilterItem = ({ icon, label, checked, onChange, count, iconStyle, iconClassName }: FilterItemProps) => (
    <label className="flex items-center justify-between w-full p-4 rounded-xl hover:bg-purple-50 transition-colors cursor-pointer border border-purple-200 bg-white">
      <div className="flex items-center gap-4">
        <span
          className={`flex-shrink-0 p-3 rounded-xl border-2 ${
            checked ? 'border-purple-500 text-purple-600 bg-purple-50' : 'border-purple-300 text-purple-400 bg-white'
          } ${iconClassName ?? ''}`}
          style={{
            width: '52px',
            height: '52px',
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            ...(iconStyle || {})
          }}>
          {isValidElement(icon)
            ? cloneElement(icon as React.ReactElement<any>, {
                className: `${(icon as any)?.props?.className ?? ''} w-6 h-6`
              })
            : icon}
        </span>
        <div>
          <span className="text-lg font-semibold text-gray-900">{label}</span>
          {count !== undefined && (
            <span className="block text-sm text-purple-600 mt-1">{count} locations nearby</span>
          )}
        </div>
      </div>
      <div className="flex items-center gap-3">
        <input
          type="checkbox"
          checked={checked}
          onChange={onChange}
          className="hidden"
        />
        <div 
          className={`relative w-7 h-7 rounded-xl border-2 transition-all cursor-pointer ${
            checked 
              ? 'bg-purple-500 border-purple-500' 
              : 'bg-white border-purple-300'
          }`}
          onClick={onChange}
        >
          {checked && (
            <svg className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 text-white w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
            </svg>
          )}
        </div>
      </div>
    </label>
  );

  return (
    <div className="h-full flex flex-col bg-purple-50">
      {/* Header - Simplified back button */}
      <div className="flex-shrink-0 border-b border-purple-200 bg-white p-4">
        {/* Title and Back Button */}
        <div className="flex items-center justify-between w-full mb-4">
          {/* Back Button - Only arrow */}
          <button
            onClick={onBack}
            className="text-purple-700 hover:text-purple-900 transition-colors"
          >
            <HiChevronLeft className="w-6 h-6" />
          </button>
          
          {/* Title */}
          <div className="flex items-center text-purple-700">
            <HiHome className="w-5 h-5 mr-2" />
            <h1 className="text-lg font-bold">Location Details</h1>
          </div>
          
          {/* Spacer for balance */}
          <div className="w-6"></div>
        </div>

        {/* Location Address */}
        <div className="text-center">
          <h1 className="text-2xl font-bold text-purple-900">{location.street}</h1>
          <p className="text-purple-600 mt-2 flex items-center gap-2 justify-center">
            <span className="bg-purple-100 text-purple-800 text-sm font-semibold px-3 py-1 rounded-full border border-purple-200">
              {location.area}
            </span>
            <span className="text-purple-400">•</span>
            <span className="font-medium text-purple-700">{location.district}</span>
          </p>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto">
        <div className="w-full max-w-full mx-auto px-4 sm:px-6 lg:px-8 space-y-6 py-6">
          {/* Price History and Facilities Map shown first */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-stretch">
            {/* Price History - Updated to handle new data format */}
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-purple-200 flex flex-col max-h-[50vh] md:max-h-[520px] overflow-auto">
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-bold text-lg text-purple-900 flex items-center gap-2">
                  <HiTrendingUp className="w-5 h-5 text-purple-500" />
                  Price Trend
                </h2>
                <div className="text-sm text-purple-600 font-medium bg-purple-100 px-3 py-1 rounded-full">
                  {priceTrend?.length || 0} months
                </div>
              </div>
              {renderPriceChart()}
            </div>

            {/* Facilities Map */}
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-purple-200 flex flex-col max-h-[50vh] md:max-h-[520px] overflow-auto">
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-bold text-lg text-purple-900 flex items-center gap-2">
                  <HiMap className="w-5 h-5 text-purple-500" />
                  Facilities Map
                </h2>
                {/* Filter Facility Button - White with purple outline */}
                <button
                  onClick={() => setShowFilterMenu(true)}
                  className="inline-flex items-center px-4 py-2 bg-white text-purple-700 rounded-xl text-sm font-semibold border-2 border-purple-300 hover:border-purple-500 hover:bg-purple-50 transition-all"
                >
                  Filter Facilities
                </button>
              </div>
              <div className="w-full rounded-xl border border-purple-100 overflow-hidden z-50" style={{ height: '400px' }}>
                <OneMapEmbedded
                  center={mapCenter}
                  zoom={13}
                  markers={facilityMarkers}
                  zoomOnly={true}
                  className="w-full h-full"
                />
              </div>
              {facilityMarkers.length > 0 && (
                <div className="mt-3 text-sm text-purple-600 bg-purple-50 px-3 py-2 rounded-lg">
                  Showing {facilityMarkers.length} facilities on map
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Filter Modal */}
      {showFilterMenu && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 overflow-auto"
          role="dialog"
          aria-modal="true"
        >
          {/* backdrop (below modal) */}
          <div
            className="fixed inset-0 bg-gray-600 bg-opacity-50 z-[9998]"
            onClick={() => setShowFilterMenu(false)}
          />

          <div
            className="relative bg-white rounded-2xl w-full max-w-md mx-auto shadow-2xl border border-purple-300 max-h-[90vh] overflow-auto z-[9999]"
            onClick={(e) => e.stopPropagation()}
          >

            {/* Header - Pale purple */}
            <div className="flex items-center justify-between p-6 border-b border-purple-200 bg-purple-100 text-purple-900 rounded-t-2xl">
              <div>
                <h3 className="text-xl font-bold">Filter Facilities</h3>
                <p className="text-purple-700 text-sm mt-1">Select amenities to show on map</p>
              </div>
              <button
                onClick={() => setShowFilterMenu(false)}
                className="p-2 hover:bg-purple-200 rounded-xl transition-colors text-purple-700 hover:text-purple-900"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="p-6 space-y-4 max-h-96 overflow-y-auto">
              {[
                { key: 'gym' as const, label: 'Fitness Centers', icon: <FaDumbbell />, count: facilityCounts.gym },
                { key: 'park' as const, label: 'Parks & Recreation', icon: <FaTree />, count: facilityCounts.park },
                { key: 'mall' as const, label: 'Shopping Malls', icon: <FaShoppingBag />, count: facilityCounts.mall },
                { key: 'school' as const, label: 'Schools', icon: <FaSchool />, count: facilityCounts.school },
                { key: 'hospital' as const, label: 'Healthcare', icon: <FaHospital />, count: facilityCounts.hospital },
                { key: 'parking' as const, label: 'Parking Lots', icon: <FaParking />, count: facilityCounts.parking },
                { key: 'dining' as const, label: 'Dining Options', icon: <FaUtensils />, count: facilityCounts.dining }
              ].map(f => (
                <FilterItem
                  key={f.key}
                  icon={f.icon}
                  label={f.label}
                  checked={selectedOptions[f.key]}
                  onChange={() => toggleOption(f.key)}
                  count={f.count}
                />
              ))}
            </div>

            <div className="flex gap-3 p-6 border-t border-purple-200 bg-purple-50 rounded-b-2xl">
              <button
                onClick={handleResetFilters}
                className="flex-1 px-4 py-3 text-purple-700 bg-white border border-purple-300 rounded-xl font-semibold hover:bg-purple-100 transition-colors"
              >
                Reset All
              </button>
              <button
                onClick={handleApplyFilters}
                disabled={loadingFacilities}
                className="flex-1 px-4 py-3 bg-gradient-to-r from-purple-500 to-purple-600 text-white rounded-xl font-semibold hover:from-purple-600 hover:to-purple-700 transition-all shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loadingFacilities ? 'Loading...' : 'Apply Filters'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DetailsView;