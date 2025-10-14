import { useState } from 'react';
import { HiChevronLeft, HiMenu, HiViewList } from 'react-icons/hi';
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import type { DragEndEvent } from '@dnd-kit/core';

interface PreferenceViewProps {
  onBack: () => void;
}

interface PreferenceCategory {
  id: string;
  name: string;
  description: string;
}

interface SortableCategoryProps {
  category: PreferenceCategory;
  index: number;
}

const SortableCategory = ({ category, index }: SortableCategoryProps) => {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: category.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  // Different gradient colors for each rank
  const getRankColor = (index: number) => {
    const colors = [
      'from-emerald-500 to-green-500',      // 1st - Emerald/Green
      'from-blue-500 to-cyan-500',          // 2nd - Blue/Cyan
      'from-purple-500 to-indigo-500',      // 3rd - Purple/Indigo
      'from-amber-500 to-orange-500',       // 4th - Amber/Orange
      'from-rose-500 to-pink-500',          // 5th - Rose/Pink
    ];
    return colors[index] || 'from-purple-500 to-purple-600';
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`flex items-center gap-4 p-4 rounded-xl border-2 transition-all duration-200 ${
        isDragging
          ? 'bg-blue-50 border-blue-300 shadow-lg'  // Blue for dragging state
          : 'bg-white border-purple-200 hover:border-blue-300 hover:bg-blue-50'  // Blue hover
      }`}
    >
      {/* Drag Handle */}
      <div 
        {...attributes}
        {...listeners}
        className="flex-shrink-0 text-blue-500 cursor-grab active:cursor-grabbing hover:text-blue-600 transition-colors"
      >
        <HiMenu className="w-5 h-5" />
      </div>

      {/* Rank Number with colored gradient */}
      <div className={`flex-shrink-0 w-8 h-8 bg-gradient-to-r ${getRankColor(index)} text-white rounded-full flex items-center justify-center font-bold text-sm shadow-sm`}>
        {index + 1}
      </div>

      {/* Category Info */}
      <div className="flex-1 min-w-0">
        <h3 className="font-bold text-gray-900 text-lg">
          {category.name}
        </h3>
      </div>
    </div>
  );
};

const PreferenceView = ({ onBack }: PreferenceViewProps) => {
  const [categories, setCategories] = useState<PreferenceCategory[]>([
    {
      id: 'affordability',
      name: 'Affordability',
      description: 'Property prices and overall cost of living'
    },
    {
      id: 'accessibility',
      name: 'Accessibility',
      description: 'Public transport and commute times'
    },
    {
      id: 'amenities',
      name: 'Amenities',
      description: 'Shopping, dining, and entertainment options'
    },
    {
      id: 'environment',
      name: 'Environment',
      description: 'Parks, greenery, and air quality'
    },
    {
      id: 'community',
      name: 'Community',
      description: 'Schools, safety, and neighborhood vibe'
    }
  ]);

  const [hasChanges, setHasChanges] = useState(false);

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;

    if (active.id !== over?.id) {
      setCategories((items) => {
        const oldIndex = items.findIndex((item) => item.id === active.id);
        const newIndex = items.findIndex((item) => item.id === over?.id);

        const newItems = arrayMove(items, oldIndex, newIndex);
        setHasChanges(true);
        return newItems;
      });
    }
  };

  const handleSavePreferences = () => {
    // Save preferences to backend or local storage
    console.log('Saved preferences:', categories);
    setHasChanges(false);
    // Show success message or handle saving logic
  };

  const handleResetToDefault = () => {
    setCategories([
      {
        id: 'affordability',
        name: 'Affordability',
        description: 'Property prices and overall cost of living'
      },
      {
        id: 'accessibility',
        name: 'Accessibility',
        description: 'Public transport and commute times'
      },
      {
        id: 'amenities',
        name: 'Amenities',
        description: 'Shopping, dining, and entertainment options'
      },
      {
        id: 'environment',
        name: 'Environment',
        description: 'Parks, greenery, and air quality'
      },
      {
        id: 'community',
        name: 'Community',
        description: 'Schools, safety, and neighborhood vibe'
      }
    ]);
    setHasChanges(false);
  };

  return (
    <div className="h-full flex flex-col bg-gradient-to-br from-purple-50 to-blue-50">
      {/* Header */}
      <div className="flex-shrink-0 border-b border-purple-200 bg-white p-4 shadow-sm">
        <div className="flex items-center justify-between w-full mb-3">
          {/* Simple back arrow button - no background, no circle */}
          <button
            onClick={onBack}
            className="text-purple-700 hover:text-purple-900 transition-colors"
          >
            <HiChevronLeft className="w-6 h-6" />
          </button>
          
          <div className="flex items-center text-purple-700">
            <HiViewList className="w-5 h-5 mr-2" />
            <h1 className="text-lg font-bold">Location Preferences</h1>
          </div>
          
          {/* Spacer for balance */}
          <div className="w-6"></div>
        </div>
        
        <p className="text-purple-600 text-sm text-center">
          Drag and drop to rank what matters most to you
        </p>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-4">
        <div className="max-w-2xl mx-auto">
          <div className="bg-white rounded-2xl p-6 border border-purple-200 shadow-lg">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-bold text-gray-900">Priority Ranking</h2>
              <div className="flex items-center text-sm text-blue-600">
                <HiViewList className="w-4 h-4 mr-1" />
                <span>Drag to reorder</span>
              </div>
            </div>

            <DndContext
              sensors={sensors}
              collisionDetection={closestCenter}
              onDragEnd={handleDragEnd}
            >
              <SortableContext items={categories} strategy={verticalListSortingStrategy}>
                <div className="space-y-3">
                  {categories.map((category, index) => (
                    <SortableCategory
                      key={category.id}
                      category={category}
                      index={index}
                    />
                  ))}
                </div>
              </SortableContext>
            </DndContext>

            {/* Instructions */}
            <div className="mt-8 p-4 bg-gradient-to-r from-blue-50 to-cyan-50 rounded-xl border border-blue-200">
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 text-sm font-bold">
                  i
                </div>
                <div>
                  <h4 className="font-semibold text-blue-900 text-sm mb-1">
                    How it works
                  </h4>
                  <p className="text-blue-700 text-sm">
                    Your top-ranked categories will have more influence on location recommendations. 
                    Drag categories up or down to match your personal preferences.
                  </p>
                </div>
              </div>
            </div>

            {/* Reset and Save Buttons */}
            <div className="flex items-center justify-center gap-4 mt-8 pt-6 border-t border-purple-200">
              <button
                onClick={handleResetToDefault}
                className="px-6 py-3 rounded-xl font-semibold transition-all border-2 border-amber-400 text-amber-700 hover:bg-amber-50 hover:border-amber-500"
              >
                Reset to Default
              </button>
              <button
                onClick={handleSavePreferences}
                disabled={!hasChanges}
                className={`px-8 py-3 rounded-xl font-semibold transition-all ${
                  hasChanges
                    ? 'bg-gradient-to-r from-green-500 to-emerald-500 text-white hover:from-green-600 hover:to-emerald-600 shadow-lg hover:shadow-xl'
                    : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                }`}
              >
                Save Preferences
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PreferenceView;