import Layout from '../components/shared/Layout';

export default function Dashboard() {
  return (
    <Layout>
      <div className="px-4 sm:px-0">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-4 text-gray-600">
          Welcome to PLC Coach! This is your dashboard.
        </p>
        <div className="mt-6 bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">
            Quick Stats
          </h2>
          <p className="text-sm text-gray-500">
            Dashboard content will be implemented in future stories.
          </p>
        </div>
      </div>
    </Layout>
  );
}
