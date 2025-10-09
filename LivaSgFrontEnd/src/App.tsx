import BottomNav from "./components/BottomNav";

function App() {
  return (
    <div className="w-screen h-screen flex items-center justify-center bg-gray-100">
      <div className="w-full max-w-sm h-full border-2 border-blue-500 rounded-xl overflow-hidden bg-white">
        <BottomNav />
      </div>
    </div>
  );
}

export default App;