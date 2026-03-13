export default function DashboardOverview() {
  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-800 mb-6">Welcome Back</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <h3 className="text-gray-500 text-sm font-medium">Today's Bookings</h3>
          <p className="text-3xl font-bold mt-2">12</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <h3 className="text-gray-500 text-sm font-medium">AI Conversations (24h)</h3>
          <p className="text-3xl font-bold mt-2">45</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <h3 className="text-gray-500 text-sm font-medium">Conversion Rate</h3>
          <p className="text-3xl font-bold mt-2">26.6%</p>
        </div>
      </div>
    </div>
  );
}
