export default function Home() {
  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md mx-auto bg-white rounded-lg shadow-md p-6">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">
            🎣 GitHub Webhook Service
          </h1>
          <p className="text-gray-600 mb-6">
            Сервис для уведомлений о GitHub обновлениях
          </p>

          <div className="bg-green-100 rounded-lg p-4 mb-6">
            <p className="text-sm text-green-700">
              <strong>✅ Статус:</strong> Webhook сервис активен
            </p>
            <p className="text-xs text-green-600 mt-2">
              Получает уведомления от GitHub и отправляет в Telegram бот
            </p>
          </div>

          <div className="bg-blue-100 rounded-lg p-4 mb-6">
            <h3 className="font-medium text-blue-900 mb-2">📡 Webhook Endpoint</h3>
            <code className="text-sm text-blue-700 bg-blue-50 px-2 py-1 rounded">
              POST /api/webhook
            </code>
          </div>

          <div className="text-sm text-gray-500">
            <h3 className="font-medium mb-2">🔄 Workflow</h3>
            <ol className="list-decimal list-inside space-y-1 text-left">
              <li>GitHub отправляет webhook при пуше</li>
              <li>Этот сервис получает уведомление</li>
              <li>Отправляется сообщение в Telegram бот</li>
              <li>Бот уведомляет администратора</li>
            </ol>
          </div>
        </div>
      </div>
    </div>
  );
}