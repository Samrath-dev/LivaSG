import { HiChevronLeft, HiDownload, HiUpload, HiCog, HiShieldCheck, HiQuestionMarkCircle, HiCode, HiTable } from 'react-icons/hi';
import { useRef, useState, useEffect } from 'react';

interface SettingsViewProps {
  onBack: () => void;
}

const SettingsView = ({ onBack }: SettingsViewProps) => {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [loading, setLoading] = useState(false);
  const showLoaderTimeout = useRef<number | null>(null);
  const loaderHideTimeout = useRef<number | null>(null);
  const [notification, setNotification] = useState<{ text: string; type: 'success' | 'error' } | null>(null);
  const [notifVisible, setNotifVisible] = useState(false);
  const notifTimeout = useRef<number | null>(null);
  const hideTimeout = useRef<number | null>(null);
  const isEnteringRef = useRef(false);

  const startLoader = () => {
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
  };

  const stopLoaderImmediate = () => {
    if (showLoaderTimeout.current) {
      window.clearTimeout(showLoaderTimeout.current);
      showLoaderTimeout.current = null;
    }
    if (loaderHideTimeout.current) {
      window.clearTimeout(loaderHideTimeout.current);
      loaderHideTimeout.current = null;
    }
    setLoading(false);
  };

  // Upload selected JSON file to backend import endpoint (backend expects JSON body)
  const processImportedFile = async (file: File) => {
    startLoader();
    try {
      const text = await file.text();

      // The import endpoint expects a JSON payload like { data: "<string>", import_type: "json" }
      const payload = {
        data: text,
        import_type: 'json'
      };

      const res = await fetch('http://localhost:8000/settings/import', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
        body: JSON.stringify(payload),
      });

      stopLoaderImmediate();
      if (!res.ok) {
        const txt = await res.text().catch(() => '');
        throw new Error(`status ${res.status} ${txt}`);
      }

      const data = await res.json().catch(() => null);
      const detail = data && typeof data === 'object' ? data : null;
      window.dispatchEvent(new CustomEvent('ranksUpdated', { detail }));
      // show inline notification instead of alert
      showNotification('Import successful', 'success');
    } catch (err) {
      stopLoaderImmediate();
      console.error('Import failed', err);
      showNotification('Failed to import data. Make sure you selected a valid .json file.', 'error');
    }
  };

  const onFileChange: React.ChangeEventHandler<HTMLInputElement> = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Only accept .json files
    const name = (file.name || '').toLowerCase();
    if (!name.endsWith('.json')) {
      showNotification('Please select a .json file for import.', 'error');
      if (fileInputRef.current) fileInputRef.current.value = '';
      return;
    }

    await processImportedFile(file);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleImport = () => {
    fileInputRef.current?.click();
  };

  const [exportModalOpen, setExportModalOpen] = useState(false);

  const handleExport = () => {
    setExportModalOpen(true);
  };

  const EXPORT_ENDPOINTS: Record<string, string> = {
    json: 'http://localhost:8000/settings/export/json',
    csv: 'http://localhost:8000/settings/export/csv',
  };

  const downloadBlob = (blob: Blob, filename: string) => {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  };

  const blobFromExportData = (format: 'json' | 'csv', data: any) => {
    if (format === 'json') {
      const filename = (data && (data.filename || 'settings.json')) || 'settings.json';
      return { blob: new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }), filename };
    }
    // csv
    const csv = typeof data.csv_data === 'string' ? data.csv_data : '';
    const filename = data.filename || 'export.csv';
    return { blob: new Blob([csv], { type: 'text/csv' }), filename };
  };

  const performExport = async (format: 'json' | 'csv') => {
    setExportModalOpen(false);
    startLoader();
    try {
      const url = EXPORT_ENDPOINTS[format];
      const res = await fetch(url);
      stopLoaderImmediate();
      if (!res.ok) throw new Error(`status ${res.status}`);
      const data = await res.json();
      const { blob, filename } = blobFromExportData(format, data);
      downloadBlob(blob, filename);
    } catch (err) {
      stopLoaderImmediate();
      console.error('Export failed', err);
      showNotification('Failed to export data', 'error');
    }
  };

  const handleResetApp = async () => {
    if (!window.confirm('Are you sure you want to reset all app data? This action cannot be undone.')) return;
    startLoader();
    try {
      // reset ranks first
      const resRanks = await fetch('http://localhost:8000/ranks/reset', { method: 'POST' });
      if (!resRanks.ok) throw new Error('Failed to reset ranks');

      // fetch saved locations to get postal codes
      const resList = await fetch('http://localhost:8000/shortlist/saved-locations');
      if (!resList.ok) throw new Error('Failed to list saved locations');
      const list = await resList.json();
      if (Array.isArray(list)) {
        // delete by postal_code for each entry (if present)
        await Promise.all(list.map(async (item: any) => {
          const pc = item?.postal_code;
          if (pc) {
            try {
              await fetch(`http://localhost:8000/shortlist/saved-locations/${encodeURIComponent(pc)}`, { method: 'DELETE' });
            } catch (_) {
              // ignore individual delete errors
            }
          }
        }));
      }

      stopLoaderImmediate();
      // tell PreferenceView to reset locally
      window.dispatchEvent(new CustomEvent('ranksReset'));
      showNotification('App data reset to default', 'success');
    } catch (err) {
      stopLoaderImmediate();
      console.error('Reset failed', err);
      showNotification('Failed to reset app data', 'error');
    }
  };

  // cleanup timers on unmount
  useEffect(() => {
    return () => {
      if (showLoaderTimeout.current) window.clearTimeout(showLoaderTimeout.current);
      if (loaderHideTimeout.current) window.clearTimeout(loaderHideTimeout.current);
      if (notifTimeout.current) window.clearTimeout(notifTimeout.current);
      if (hideTimeout.current) window.clearTimeout(hideTimeout.current);
    };
  }, []);

  const showNotification = (text: string, type: 'success' | 'error') => {
    if (notifTimeout.current) window.clearTimeout(notifTimeout.current);
    if (hideTimeout.current) window.clearTimeout(hideTimeout.current);

    setNotification({ text, type });
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
  };

  return (
    <div className="h-full flex flex-col bg-purple-50">
      {/* Hidden file input used for Import Data */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".json,application/json"
        onChange={onFileChange}
        className="hidden"
      />

      {/* Loading overlay (same style as PreferenceView) */}
      {loading && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-black bg-opacity-40">
          <div className="w-14 h-14 rounded-full border-4 border-white border-t-transparent animate-spin" />
        </div>
      )}
      {/* Export format modal */}
      {exportModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black bg-opacity-50" onClick={() => setExportModalOpen(false)} />
          <div className="relative bg-white rounded-xl p-6 w-80 shadow-xl z-10 text-center">
            <h3 className="text-lg font-semibold mb-4">Export format</h3>
            <div className="space-y-3">
              <button
                onClick={() => performExport('json')}
                className="w-full flex items-center justify-center gap-3 px-4 py-3 border-2 border-blue-400 rounded-lg hover:bg-blue-50 text-base font-semibold text-gray-900"
              >
                <HiCode className="w-5 h-5 text-blue-500" />
                <span>JSON</span>
              </button>
              <button
                onClick={() => performExport('csv')}
                className="w-full flex items-center justify-center gap-3 px-4 py-3 border-2 border-green-400 rounded-lg hover:bg-green-50 text-base font-semibold text-gray-900"
              >
                <HiTable className="w-5 h-5 text-green-500" />
                <span>CSV</span>
              </button>
              
            </div>
            <div className="mt-4">
              <button onClick={() => setExportModalOpen(false)} className="text-sm text-gray-600">Cancel</button>
            </div>
          </div>
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
          
          {/* Centered title */}
          <div className="flex items-center text-purple-700">
            <HiCog className="w-5 h-5 mr-2" />
            <h1 className="text-lg font-bold">Settings</h1>
          </div>
        </div>
        
        <p className="text-purple-600 text-sm text-center">
          Manage your app preferences and data
        </p>
      </div>

      {/* Slide-down overlay notification: positioned below header */}
      <div
        aria-live="polite"
        className={`fixed left-0 right-0 top-24 z-50 flex justify-center pointer-events-none transition-transform transition-opacity duration-300 ${
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
        <div className="max-w-2xl mx-auto space-y-6">
          {/* Import/Export Section */}
          <div className="bg-white rounded-2xl p-6 border border-purple-200 shadow-lg">
            <h2 className="text-lg font-bold text-gray-900 mb-4">Data Management</h2>
            
            <div className="flex gap-4 mb-4">
              <button
                onClick={handleImport}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-xl font-semibold hover:from-blue-600 hover:to-purple-600 transition-all shadow-lg hover:shadow-xl"
              >
                <HiUpload className="w-5 h-5" />
                Import Data
              </button>
              
              <button
                onClick={handleExport}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-green-500 to-emerald-500 text-white rounded-xl font-semibold hover:from-green-600 hover:to-emerald-600 transition-all shadow-lg hover:shadow-xl"
              >
                <HiDownload className="w-5 h-5" />
                Export Data
              </button>
            </div>
            
            <p className="text-sm text-purple-600 text-center">
              Import previous data to start where you last left off or Export for future use
            </p>
          </div>

          {/* Support Section */}
          <div className="bg-white rounded-2xl p-6 border border-purple-200 shadow-lg">
            <h2 className="text-lg font-bold text-gray-900 mb-4">Support</h2>
            
            <div className="space-y-3">
              <button className="w-full flex items-center gap-3 p-3 rounded-lg border border-purple-100 hover:bg-purple-50 transition-colors text-left">
                <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center text-blue-600">
                  <HiQuestionMarkCircle className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">Help & Support</h3>
                  <p className="text-sm text-gray-600">Get help using the app</p>
                </div>
              </button>

              <button className="w-full flex items-center gap-3 p-3 rounded-lg border border-purple-100 hover:bg-purple-50 transition-colors text-left">
                <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center text-green-600">
                  <HiShieldCheck className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">Privacy Policy</h3>
                  <p className="text-sm text-gray-600">How we handle your data</p>
                </div>
              </button>

              <button 
                onClick={handleResetApp}
                className="w-full flex items-center gap-3 p-3 rounded-lg border border-amber-100 hover:bg-amber-50 transition-colors text-left"
              >
                <div className="w-10 h-10 bg-amber-100 rounded-full flex items-center justify-center text-amber-600">
                  <HiShieldCheck className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-semibold text-amber-700">Reset App Data</h3>
                  <p className="text-sm text-amber-600">Clear all your preferences and data</p>
                </div>
              </button>
            </div>
          </div>

          {/* App Info */}
          <div className="text-center py-4">
            <p className="text-sm text-purple-600">
              App Version 3.1.4
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsView;