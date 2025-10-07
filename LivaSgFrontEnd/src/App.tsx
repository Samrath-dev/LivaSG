function App() {
  return (
    <div className="w-screen h-screen flex items-center justify-center bg-gray-100">
      {/* Dynamic container */}
      <div className="w-full max-w-sm h-full border-2 border-blue-500 rounded-xl overflow-auto bg-white">
        <div className="p-4">
          <h1 className="text-lg font-bold">Dynamic Mobile Container</h1>
          <p className="text-sm text-gray-600">
            Resize the window or use Chrome DevTools mobile view to test.
          </p>
          <button className="mt-4 px-4 py-2 bg-blue-500 text-white rounded-lg">
            Test Button
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;
