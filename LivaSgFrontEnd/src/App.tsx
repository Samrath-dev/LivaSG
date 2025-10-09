import BottomNav from "./components/BottomNav";

function App() {
  return (
    <div className="w-screen h-screen flex items-center justify-center bg-gray-100 p-4">
      {/* Dynamic mobile container */}
      <div className="w-full h-full max-w-sm max-h-[800px] min-h-[600px] border-2 border-blue-500 rounded-xl overflow-hidden bg-white shadow-lg transition-all duration-300">
        <BottomNav />
      </div>
    </div>
  );
}

export default App;