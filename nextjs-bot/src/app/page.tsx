"use client";

import { useState } from 'react';

export default function Home() {
  const [status, setStatus] = useState<{ type: 'success' | 'error' | 'info'; message: string } | null>(null);
  const [loading, setLoading] = useState(false);

  const callApi = async (url: string, method: string = 'POST') => {
    setLoading(true);
    setStatus({ type: 'info', message: 'Выполняется запрос...' });

    try {
      const res = await fetch(url, { method });
      const data = await res.json();

      if (res.ok) {
        setStatus({ type: 'success', message: JSON.stringify(data, null, 2) });
      } else {
        setStatus({ type: 'error', message: data.error || 'Произошла ошибка' });
      }
    } catch (e: any) {
      setStatus({ type: 'error', message: e.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md mx-auto bg-white rounded-lg shadow-md p-6">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">
            🤖 Money Bot Dashboard
          </h1>
          <p className="text-gray-600 mb-6">
            Панель управления Telegram ботом на Next.js
          </p>

          <div className="bg-green-100 rounded-lg p-4 mb-6">
            <p className="text-sm text-green-700">
              <strong>✅ Статус:</strong> Приложение успешно развернуто на Vercel!
            </p>
          </div>

          <div className="space-y-4">
            <button
              onClick={() => callApi('/api/setup-webhook', 'POST')}
              disabled={loading}
              className="block w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-medium py-2 px-4 rounded-lg transition duration-200 text-center"
            >
              🔧 Настроить вебхук
            </button>

            <button
              onClick={() => callApi('/api/seed', 'POST')}
              disabled={loading}
              className="block w-full bg-green-600 hover:bg-green-700 disabled:bg-green-400 text-white font-medium py-2 px-4 rounded-lg transition duration-200 text-center"
            >
              🌱 Заполнить базу данных
            </button>

            <button
              onClick={() => callApi('/api/setup-webhook', 'DELETE')}
              disabled={loading}
              className="block w-full bg-red-600 hover:bg-red-700 disabled:bg-red-400 text-white font-medium py-2 px-4 rounded-lg transition duration-200 text-center"
            >
              🗑️ Удалить вебхук
            </button>
          </div>

          {status && (
            <div className={`mt-6 p-4 rounded text-sm text-left font-mono overflow-auto max-h-40 ${status.type === 'success' ? 'bg-green-50 text-green-800' :
                status.type === 'error' ? 'bg-red-50 text-red-800' : 'bg-gray-100 text-gray-800'
              }`}>
              {status.message}
            </div>
          )}

          <div className="mt-8 text-sm text-gray-500">
            <h3 className="font-medium mb-2">🚀 Следующие шаги:</h3>
            <ol className="list-decimal list-inside space-y-1 text-left">
              <li>Нажмите "🔧 Настроить вебхук" для подключения бота</li>
              <li>Нажмите "🌱 Заполнить базу данных" для инициализации</li>
              <li>Проверьте работу бота в Telegram</li>
            </ol>
          </div>

          <div className="mt-6 text-xs text-gray-400">
            <p>🎯 Деплой завершен успешно! Бот готов к работе.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
