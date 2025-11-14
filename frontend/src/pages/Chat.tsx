import Layout from '../components/shared/Layout';

export default function Chat() {
  return (
    <Layout>
      <div className="px-4 sm:px-0">
        <h1 className="text-3xl font-bold text-gray-900">Chat</h1>
        <p className="mt-4 text-gray-600">
          Chat with your AI PLC Coach.
        </p>
        <div className="mt-6 bg-white shadow rounded-lg p-6 min-h-[400px]">
          <p className="text-sm text-gray-500">
            Chat interface will be implemented in Epic 2.
          </p>
        </div>
      </div>
    </Layout>
  );
}
