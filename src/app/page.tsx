'use client';

import { useState, useEffect } from 'react';

export default function Home() {
  const [status, setStatus] = useState('Загрузка...');
  const [isLoading, setIsLoading] = useState(false);

  const setupWebhook = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/setup-webhook', { method: 'POST' });
      const data = await response.json();
      if (data.success) {
        setStatus('✅ Вебхук успешно настроен');
      } else {
        setStatus('❌ Ошибка настройки вебхука');
      }
    } catch (error) {
      setStatus('❌ Ошибка настройки вебхука');
    }
    setIsLoading(false);
  };

  const seedDatabase = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/seed', { method: 'POST' });
      const data = await response.json();
      if (data.success) {
        setStatus('✅ База данных заполнена');
      } else {
        setStatus('❌ Ошибка заполнения базы данных');
      }
    } catch (error) {
      setStatus('❌ Ошибка заполнения базы данных');
    }
    setIsLoading(false);
  };

  const deleteWebhook = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/setup-webhook', { method: 'DELETE' });
      const data = await response.json();
      if (data.success) {
        setStatus('✅ Вебхук удален');
      } else {
        setStatus('❌ Ошибка удаления вебхука');
      }
    } catch (error) {
      setStatus('❌ Ошибка удаления вебхука');
    }
    setIsLoading(false);
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

          <div className="bg-gray-100 rounded-lg p-4 mb-6">
            <p className="text-sm text-gray-700">
              <strong>Статус:</strong> {status}
            </p>
          </div>

          <div className="space-y-4">
            <button
              onClick={setupWebhook}
              disabled={isLoading}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-medium py-2 px-4 rounded-lg transition duration-200"
            >
              {isLoading ? '⏳ Настройка...' : '🔧 Настроить вебхук'}
            </button>

            <button
              onClick={seedDatabase}
              disabled={isLoading}
              className="w-full bg-green-600 hover:bg-green-700 disabled:bg-green-400 text-white font-medium py-2 px-4 rounded-lg transition duration-200"
            >
              {isLoading ? '⏳ Заполнение...' : '🌱 Заполнить базу данных'}
            </button>

            <button
              onClick={deleteWebhook}
              disabled={isLoading}
              className="w-full bg-red-600 hover:bg-red-700 disabled:bg-red-400 text-white font-medium py-2 px-4 rounded-lg transition duration-200"
            >
              {isLoading ? '⏳ Удаление...' : '🗑️ Удалить вебхук'}
            </button>
          </div>

          <div className="mt-8 text-sm text-gray-500">
            <h3 className="font-medium mb-2">Инструкция по развертыванию:</h3>
            <ol className="list-decimal list-inside space-y-1 text-left">
              <li>Запустите проект локально: <code className="bg-gray-100 px-1 rounded">npm run dev</code></li>
              <li>Заполните базу данных</li>
              <li>Настройте переменные окружения на Vercel</li>
              <li>Разверните на Vercel</li>
              <li>Настройте вебхук через кнопку выше</li>
            </ol>
          </div>

          <div className="mt-6 text-xs text-gray-400">
            <p>Не забудьте настроить переменные окружения:</p>
            <ul className="mt-1 space-y-1">
              <li><code>BOT_TOKEN</code> - токен Telegram бота</li>
              <li><code>DATABASE_URL</code> - URL базы данных</li>
              <li><code>NEXT_PUBLIC_APP_URL</code> - URL вашего приложения</li>
              <li><code>WEBHOOK_SECRET</code> - секрет для вебхука</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
