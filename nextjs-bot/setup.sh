#!/bin/bash

echo "🚀 Настройка Money Bot (Next.js)"

# Проверка наличия Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js не установлен. Установите Node.js версии 18+"
    exit 1
fi

# Проверка наличия npm
if ! command -v npm &> /dev/null; then
    echo "❌ npm не установлен. Установите npm"
    exit 1
fi

echo "📦 Установка зависимостей..."
npm install

echo "🗄️ Настройка базы данных..."
npx prisma generate
npx prisma migrate dev --name init

echo "🌱 Заполнение базы данных начальными данными..."
node -e "
import { seedDatabase } from './src/utils/seed-database.ts';
seedDatabase().then(() => {
  console.log('✅ База данных заполнена');
  process.exit(0);
}).catch((error) => {
  console.error('❌ Ошибка:', error);
  process.exit(1);
});
"

echo "✅ Настройка завершена!"
echo ""
echo "📝 Следующие шаги:"
echo "1. Создайте файл .env.local (смотрите SETUP_ENV.txt)"
echo "2. Запустите проект: npm run dev"
echo "3. Откройте http://localhost:3000 для настройки вебхука"
echo ""
echo "🎉 Готово к развертыванию на Vercel!"

