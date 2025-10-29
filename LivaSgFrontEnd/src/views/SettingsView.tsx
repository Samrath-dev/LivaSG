import { HiChevronLeft, HiDownload, HiUpload, HiCog, HiShieldCheck, HiQuestionMarkCircle } from 'react-icons/hi';
import { useRef } from 'react';

interface SettingsViewProps {
  onBack: () => void;
}

const SettingsView = ({ onBack }: SettingsViewProps) => {
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const processImportedCsv = async (text: string) => {
    const lines = text.split(/\r?\n/).map((l) => l.trim()).filter(Boolean);
    if (lines.length === 0) return;
    const start = lines[0].toLowerCase().startsWith('key') ? 1 : 0;
    const obj: Record<string, number> = {};
    for (let i = start; i < lines.length; i++) {
      const parts = lines[i].split(',').map(p => p.trim());
      if (parts.length >= 2) {
        const key = parts[0];
        const val = Number(parts[1]);
        if (!Number.isNaN(val)) obj[key] = val;
      }
    }
    if (!Object.keys(obj).length) {
      alert('No valid rows found in CSV');
      return;
    }

    try {
      const res = await fetch('http://localhost:8000/ranks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(obj),
      });
      if (!res.ok) throw new Error(`status ${res.status}`);
      // notify PreferenceView to reload/update
      window.dispatchEvent(new CustomEvent('ranksUpdated', { detail: obj }));
      alert('Imported ranks and updated backend');
    } catch (err) {
      console.error('Import failed', err);
      alert('Failed to import ranks');
    }
  };

  const onFileChange: React.ChangeEventHandler<HTMLInputElement> = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const text = await file.text();
    await processImportedCsv(text);
    // reset input
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleImport = () => {
    fileInputRef.current?.click();
    console.log('Import clicked');
    // This would typically open a file picker
  };

  const handleExport = () => {
    (async () => {
      try {
        const res = await fetch('http://localhost:8000/ranks');
        if (!res.ok) throw new Error(`status ${res.status}`);
        const data = await res.json();
        const payload = data && data.ranks && typeof data.ranks === 'object' ? data.ranks : data;
        const rows = Object.entries(payload || {}).map(([k, v]) => `${k},${v}`);
        const csv = ['key,value', ...rows].join('\n');
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'ranks.csv';
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
      } catch (err) {
        console.error('Export failed', err);
        alert('Failed to export ranks');
      }
    })();
    console.log('Export clicked');
    // This would typically trigger a file download
  };

  const handleResetApp = () => {
    if (!window.confirm('Are you sure you want to reset all app data? This action cannot be undone.')) return;
    (async () => {
      try {
        const res = await fetch('http://localhost:8000/ranks/reset', { method: 'POST' });
        if (!res.ok) throw new Error(`status ${res.status}`);
        window.dispatchEvent(new CustomEvent('ranksReset'));
        alert('App data reset to default');
      } catch (err) {
        console.error('Reset failed', err);
        alert('Failed to reset app data');
      }
    })();
  };

  return (
    <div className="h-full flex flex-col bg-purple-50">
      {/* Hidden file input used for Import Data */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".csv,text/csv"
        onChange={onFileChange}
        className="hidden"
      />
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
              App Version 1.0.0
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsView;