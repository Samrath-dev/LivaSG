import React from 'react';
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

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-[100]"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-2xl w-full max-w-3xl p-6 shadow-lg"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold text-purple-900">Comparison Overview</h2>
          <button onClick={onClose} className="text-sm text-purple-600 hover:text-purple-900">Close</button>
        </div>

        <div className="bg-purple-50 p-4 rounded-xl" style={{ height: 360 }}>
          <Radar data={data} options={options} height={320} />
        </div>

        <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
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
  );
}