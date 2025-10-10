import { useState } from 'react';
import mapDummy from '../assets/mapDummy.png'; 

const MapView = () => {
  const [searchQuery, setSearchQuery] = useState('');

  return (
    <div className="h-full flex flex-col">
      <div className="flex-1 bg-gray-100 relative pt-16">
        <div className="w-full h-full">
          <img 
            src={mapDummy} 
            alt="Map placeholder"
            className="w-full h-full object-cover"
          />
          
          {searchQuery && (
            <div className="absolute top-4 left-4 bg-black bg-opacity-70 text-white px-3 py-2 rounded-lg">
              <p className="text-sm">Search: {searchQuery}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MapView;