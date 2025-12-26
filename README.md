# 🎣 GitHub Webhook Service

Простой сервис для получения webhook уведомлений от GitHub и отправки уведомлений в Telegram бот.

## 🚀 Быстрое развертывание

### 1. Клонировать и установить
```bash
git clone https://github.com/Allexndr/money_bot.git -b webhook-service
cd webhook-service
npm install
```

### 2. Настроить переменные окружения
В Vercel добавьте переменные:
```
BOT_TOKEN=8300376368:AAGGP6Ln1f0QNoNHQr0xOxpmXzJBIHSpkhg
ADMIN_CHAT_ID=5450018125
```

### 3. Развернуть на Vercel
```bash
vercel --prod
```

## 🎯 Как работает

1. **GitHub** отправляет webhook при пуше в репозиторий
2. **Этот сервис** получает уведомление на `/api/webhook`
3. **Telegram бот** получает сообщение с информацией о коммитах
4. **Администратор** видит уведомление в Telegram

## 📡 Webhook URL

После развертывания на Vercel, URL будет выглядеть так:
```
https://your-app-name.vercel.app/api/webhook
```

## 🔧 Настройка GitHub

1. Перейти в репозиторий → **Settings** → **Webhooks**
2. **Add webhook**:
   - **Payload URL**: `https://your-app-name.vercel.app/api/webhook`
   - **Content type**: `application/json`
   - **Events**: `Pushes`
   - **Branch**: `python-version` (или нужная ветка)

## 📱 Что получает бот

При каждом пуше бот получает сообщение:
```
🚀 GitHub Update

📦 Repository: money_bot
🌿 Branch: python-version
📝 Commits: 2

📋 Changes:
1. a1b2c3d - Added new feature
2. e4f5g6h - Fixed bug
```

## ✅ Проверка работы

Посетите главную страницу сервиса для проверки статуса.
