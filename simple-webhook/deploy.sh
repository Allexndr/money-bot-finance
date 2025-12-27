#!/bin/bash

echo "🚀 Развертывание GitHub Webhook Service на Vercel"
echo ""

# Проверяем наличие Vercel CLI
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI не установлен. Установите его:"
    echo "npm install -g vercel"
    exit 1
fi

# Логинимся в Vercel (если не залогинены)
echo "🔑 Проверяем авторизацию в Vercel..."
vercel login

# Развертываем
echo "📦 Развертываем на Vercel..."
vercel --prod

echo ""
echo "✅ Развертывание завершено!"
echo ""
echo "📋 Следующие шаги:"
echo "1. Перейдите в Vercel Dashboard"
echo "2. Добавьте переменные окружения:"
echo "   BOT_TOKEN=8300376368:AAGGP6Ln1f0QNoNHQr0xOxpmXzJBIHSpkhg"
echo "   ADMIN_CHAT_ID=5450018125"
echo "3. Скопируйте URL вашего приложения"
echo "4. Настройте webhook в GitHub:"
echo "   - URL: https://your-app-name.vercel.app/api/webhook"
echo "   - Content type: application/json"
echo "   - Events: Pushes"
echo "   - Branch: python-version"
