const ComparisonView = () => {
  return (
    <div style={{ height: '100%', padding: '20px', background: 'black' }}>
      <h1>Comparison View</h1>
      <div style={{ height: '1500px' }}>
        <p>Different content length - bottom nav should stay in same position</p>
        {Array.from({ length: 30 }).map((_, i) => (
          <div key={i}>Comparison item {i + 1}</div>
        ))}
      </div>
    </div>
  );
};

export default ComparisonView;