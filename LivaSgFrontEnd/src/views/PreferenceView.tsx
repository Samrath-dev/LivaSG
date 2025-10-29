import { useState, useRef, useEffect } from 'react';
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

const DEFAULT_CATEGORIES: PreferenceCategory[] = [
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
];

// Persistant color mapping per category id so colors don't change when reordered
const CATEGORY_COLORS: Record<string, string> = {
  affordability: 'from-emerald-500 to-green-500',   // affordability always emerald/green
  accessibility: 'from-blue-500 to-cyan-500',       // accessibility always blue/cyan
  amenities: 'from-purple-500 to-indigo-500',      // amenities always purple/indigo
  environment: 'from-amber-500 to-orange-500',     // environment always amber/orange
  community: 'from-rose-500 to-pink-500',           // community always rose/pink
};

// Map category id -> API key
const RANK_KEY_MAP: Record<string, string> = {
  affordability: 'rAff',
  accessibility: 'rAcc',
  amenities: 'rAmen',
  environment: 'rEnv',
  community: 'rCom',
};

const sendRankUpdate = async (items: PreferenceCategory[]): Promise<boolean> => {
  const body: Record<string, number> = {};
  items.forEach((it, idx) => {
    const key = RANK_KEY_MAP[it.id];
    if (key) body[key] = idx + 1;
  });

  try {
    const res = await fetch('http://localhost:8000/ranks', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      console.error('Failed to update ranks:', res.status, await res.text());
      return false;
    }
    return true;
  } catch (err) {
    console.error('Error sending rank update:', err);
    return false;
  }
};

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

  const colorClass = CATEGORY_COLORS[category.id] || 'from-purple-500 to-purple-600';

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
      <div className={`flex-shrink-0 w-8 h-8 bg-gradient-to-r ${colorClass} text-white rounded-full flex items-center justify-center font-bold text-sm shadow-sm`}>
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
  const [categories, setCategories] = useState<PreferenceCategory[]>(DEFAULT_CATEGORIES);
  const [notification, setNotification] = useState<{ text: string; type: 'success' | 'error' } | null>(null);
  const [notifVisible, setNotifVisible] = useState(false);
  const notifTimeout = useRef<number | null>(null);
  const hideTimeout = useRef<number | null>(null);
  const isEnteringRef = useRef(false);
  const [loading, setLoading] = useState(false);
  const showLoaderTimeout = useRef<number | null>(null);
  const loaderHideTimeout = useRef<number | null>(null);

  useEffect(() => {
    return () => {
      if (notifTimeout.current) window.clearTimeout(notifTimeout.current);
      if (hideTimeout.current) window.clearTimeout(hideTimeout.current);
      if (showLoaderTimeout.current) window.clearTimeout(showLoaderTimeout.current);
      if (loaderHideTimeout.current) window.clearTimeout(loaderHideTimeout.current);
    };
  }, []);

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

   const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;

    if (active.id !== over?.id) {
      const oldIndex = categories.findIndex((item) => item.id === active.id);
      const newIndex = categories.findIndex((item) => item.id === over?.id);

      const newItems = arrayMove(categories, oldIndex, newIndex);
      setCategories(newItems);

      if (showLoaderTimeout.current) window.clearTimeout(showLoaderTimeout.current);
      showLoaderTimeout.current = window.setTimeout(() => {
        setLoading(true);
        if (loaderHideTimeout.current) window.clearTimeout(loaderHideTimeout.current);
        loaderHideTimeout.current = window.setTimeout(() => {
          setLoading(false);
          loaderHideTimeout.current = null;
        }, 3000);
        showLoaderTimeout.current = null;
      }, 500);

      const ok = await sendRankUpdate(newItems);

      if (showLoaderTimeout.current) {
        window.clearTimeout(showLoaderTimeout.current);
        showLoaderTimeout.current = null;
      }
      if (loaderHideTimeout.current) {
        window.clearTimeout(loaderHideTimeout.current);
        loaderHideTimeout.current = null;
      }
      setLoading(false);

      await new Promise<void>((resolve) =>
        requestAnimationFrame(() => requestAnimationFrame(() => resolve()))
      );

      if (notifTimeout.current) window.clearTimeout(notifTimeout.current);
      if (hideTimeout.current) window.clearTimeout(hideTimeout.current);

      setNotification(ok ? { text: 'Ranking Updated!', type: 'success' } : { text: 'Failed to update ranking', type: 'error' });
      isEnteringRef.current = true;
      setNotifVisible(false);
      requestAnimationFrame(() => {
        isEnteringRef.current = false;
        setNotifVisible(true);
      });

      notifTimeout.current = window.setTimeout(() => {
        setNotifVisible(false);
        hideTimeout.current = window.setTimeout(() => setNotification(null), 300);
      }, 3000);
    }
  };

  const handleResetToDefault = async () => {
    if (notifTimeout.current) window.clearTimeout(notifTimeout.current);
    if (hideTimeout.current) window.clearTimeout(hideTimeout.current);
    if (showLoaderTimeout.current) window.clearTimeout(showLoaderTimeout.current);

    try {
      if (showLoaderTimeout.current) window.clearTimeout(showLoaderTimeout.current);
      showLoaderTimeout.current = window.setTimeout(() => {
        setLoading(true);
        if (loaderHideTimeout.current) window.clearTimeout(loaderHideTimeout.current);
        loaderHideTimeout.current = window.setTimeout(() => {
          setLoading(false);
          loaderHideTimeout.current = null;
        }, 3000);
        showLoaderTimeout.current = null;
      }, 500);

      const res = await fetch('http://localhost:8000/ranks/reset', { method: 'POST' });
      const ok = res.ok;

      if (showLoaderTimeout.current) {
        window.clearTimeout(showLoaderTimeout.current);
        showLoaderTimeout.current = null;
      }
      if (loaderHideTimeout.current) {
        window.clearTimeout(loaderHideTimeout.current);
        loaderHideTimeout.current = null;
      }
      setLoading(false);

      await new Promise<void>((resolve) =>
        requestAnimationFrame(() => requestAnimationFrame(() => resolve()))
      );

      setCategories(DEFAULT_CATEGORIES);

      setNotification(ok ? { text: 'Ranking reset to default', type: 'success' } : { text: 'Failed to reset ranking', type: 'error' });
      isEnteringRef.current = true;
      setNotifVisible(false);
      requestAnimationFrame(() => {
        isEnteringRef.current = false;
        setNotifVisible(true);
      });

      notifTimeout.current = window.setTimeout(() => {
        setNotifVisible(false);
        hideTimeout.current = window.setTimeout(() => setNotification(null), 300);
      }, 3000);
    } catch (err) {
      console.error('Error resetting ranks:', err);
      if (showLoaderTimeout.current) {
        window.clearTimeout(showLoaderTimeout.current);
        showLoaderTimeout.current = null;
      }
      if (loaderHideTimeout.current) {
        window.clearTimeout(loaderHideTimeout.current);
        loaderHideTimeout.current = null;
      }
      setLoading(false);

      await new Promise<void>((resolve) =>
        requestAnimationFrame(() => requestAnimationFrame(() => resolve()))
      );

      setNotification({ text: 'Failed to reset ranking', type: 'error' });
      isEnteringRef.current = true;
      setNotifVisible(false);
      requestAnimationFrame(() => {
        isEnteringRef.current = false;
        setNotifVisible(true);
      });
      notifTimeout.current = window.setTimeout(() => {
        setNotifVisible(false);
        hideTimeout.current = window.setTimeout(() => setNotification(null), 300);
      }, 3000);
    }
  };

  return (
    <div className="h-full flex flex-col bg-purple-50">

      {/* Loading overlay (dims screen) */}
      {loading && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-black bg-opacity-40">
          <div className="w-14 h-14 rounded-full border-4 border-white border-t-transparent animate-spin" />
        </div>
      )}

      {/* Header */}
      <div className="flex-shrink-0 border-b border-purple-200 bg-white p-4">
        <div className="flex items-center justify-center w-full mb-3 relative">
          {/* Back button positioned absolutely on the left */}
          <button
            onClick={onBack}
            className="absolute left-0 text-purple-700 hover:text-purple-900 transition-colors"
          >
            <HiChevronLeft className="w-6 h-6" />
          </button>
          
          {/* Centered title and icon */}
          <div className="flex items-center text-purple-700">
            <HiViewList className="w-5 h-5 mr-2" />
            <h1 className="text-lg font-bold">Location Preferences</h1>
          </div>
        </div>
        
        <p className="text-purple-600 text-sm text-center">
          Drag and drop to rank what matters most to you
        </p>
      </div>

      {/* Slide-down overlay notification: positioned below header */}
      <div
        aria-live="polite"
        className={`fixed left-0 right-0 top-32 z-50 flex justify-center pointer-events-none transition-transform transition-opacity duration-300 ${
          isEnteringRef.current ? '-translate-y-6' : 'translate-y-0'
        } ${notifVisible ? 'opacity-100' : 'opacity-0'}`}
      >
        {notification && (
          <div
            className={`pointer-events-auto max-w-2xl mx-4 p-3 rounded-lg text-center shadow-md ${
              notification.type === 'success'
                ? 'bg-green-50 text-green-800 border border-green-200'
                : 'bg-red-50 text-red-800 border border-red-200'
            }`}
          >
            {notification.text}
          </div>
        )}
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
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PreferenceView;