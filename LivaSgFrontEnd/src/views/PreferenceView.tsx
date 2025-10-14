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
  icon: string;
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

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`flex items-center gap-4 p-4 rounded-xl border-2 transition-all duration-200 ${
        isDragging
          ? 'bg-purple-50 border-purple-300 shadow-lg'
          : 'bg-white border-purple-200 hover:border-purple-300 hover:bg-purple-50'
      }`}
    >
      {/* Drag Handle */}
      <div 
        {...attributes}
        {...listeners}
        className="flex-shrink-0 text-purple-400 cursor-grab active:cursor-grabbing"
      >
        <HiMenu className="w-5 h-5" />
      </div>

      {/* Rank Number */}
      <div className="flex-shrink-0 w-8 h-8 bg-gradient-to-r from-purple-500 to-purple-600 text-white rounded-full flex items-center justify-center font-bold text-sm">
        {index + 1}
      </div>

      {/* Category Icon */}
      <div className="flex-shrink-0 w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center text-xl">
        {category.icon}
      </div>

      {/* Category Info */}
      <div className="flex-1 min-w-0">
        <h3 className="font-bold text-purple-900 text-lg">
          {category.name}
        </h3>
      </div>

      {/* Priority Badge */}
      <div className="flex-shrink-0">
        <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
          index === 0
            ? 'bg-green-100 text-green-800'
            : index === 1
            ? 'bg-blue-100 text-blue-800'
            : index === 2
            ? 'bg-purple-100 text-purple-800'
            : 'bg-gray-100 text-gray-800'
        }`}>
          {index === 0 && 'Highest Priority'}
          {index === 1 && 'High Priority'}
          {index === 2 && 'Medium Priority'}
          {index >= 3 && 'Lower Priority'}
        </span>
      </div>
    </div>
  );
};

const PreferenceView = ({ onBack }: PreferenceViewProps) => {
  const [categories, setCategories] = useState<PreferenceCategory[]>([
    {
      id: 'affordability',
      name: 'Affordability',
      description: 'Property prices and overall cost of living',
      icon: '💰'
    },
    {
      id: 'accessibility',
      name: 'Accessibility',
      description: 'Public transport and commute times',
      icon: '🚆'
    },
    {
      id: 'amenities',
      name: 'Amenities',
      description: 'Shopping, dining, and entertainment options',
      icon: '🏪'
    },
    {
      id: 'environment',
      name: 'Environment',
      description: 'Parks, greenery, and air quality',
      icon: '🌳'
    },
    {
      id: 'community',
      name: 'Community',
      description: 'Schools, safety, and neighborhood vibe',
      icon: '👨‍👩‍👧‍👦'
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
        description: 'Property prices and overall cost of living',
        icon: '💰'
      },
      {
        id: 'accessibility',
        name: 'Accessibility',
        description: 'Public transport and commute times',
        icon: '🚆'
      },
      {
        id: 'amenities',
        name: 'Amenities',
        description: 'Shopping, dining, and entertainment options',
        icon: '🏪'
      },
      {
        id: 'environment',
        name: 'Environment',
        description: 'Parks, greenery, and air quality',
        icon: '🌳'
      },
      {
        id: 'community',
        name: 'Community',
        description: 'Schools, safety, and neighborhood vibe',
        icon: '👨‍👩‍👧‍👦'
      }
    ]);
    setHasChanges(false);
  };

  return (
    <div className="h-full flex flex-col bg-purple-50">
      {/* Header */}
      <div className="flex-shrink-0 border-b border-purple-200 bg-white p-4">
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
          
          <div className="flex items-center gap-3">
            <button
              onClick={handleResetToDefault}
              className="text-purple-600 hover:text-purple-800 font-medium px-3 py-2 rounded-lg hover:bg-purple-50 transition-colors"
            >
              Reset
            </button>
            <button
              onClick={handleSavePreferences}
              disabled={!hasChanges}
              className={`px-4 py-2 rounded-xl font-semibold transition-all ${
                hasChanges
                  ? 'bg-purple-600 text-white hover:bg-purple-700'
                  : 'bg-gray-300 text-gray-500 cursor-not-allowed'
              }`}
            >
              Save
            </button>
          </div>
        </div>
        
        <p className="text-purple-600 text-sm text-center">
          Drag and drop to rank what matters most to you
        </p>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-4">
        <div className="max-w-2xl mx-auto">
          <div className="bg-white rounded-2xl p-6 border border-purple-200">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-bold text-purple-900">Priority Ranking</h2>
              <div className="flex items-center text-sm text-purple-600">
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
            <div className="mt-8 p-4 bg-purple-50 rounded-xl border border-purple-200">
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 w-6 h-6 bg-purple-100 rounded-full flex items-center justify-center text-purple-600 text-sm font-bold">
                  i
                </div>
                <div>
                  <h4 className="font-semibold text-purple-900 text-sm mb-1">
                    How it works
                  </h4>
                  <p className="text-purple-700 text-sm">
                    Your top-ranked categories will have more influence on location recommendations. 
                    Drag categories up or down to match your personal preferences.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PreferenceView;