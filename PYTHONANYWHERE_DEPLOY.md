# 🚀 Автоматизация деплоя на PythonAnywhere

## 📋 Предварительная настройка

### 1. **Инициализируйте Git на PythonAnywhere**
```bash
# В консоли PythonAnywhere
cd /home/your-username/
git clone https://github.com/your-username/your-repo.git your-project
cd your-project
```

### 2. **Загрузите скрипт деплоя**
Скопируйте содержимое `deploy.sh` на PythonAnywhere в корень проекта.

## 🔄 Способы автоматизации

### **Способ 1: Cron Job (рекомендуется)**

1. **В PythonAnywhere Dashboard → Tasks → Schedule**
2. **Добавьте задачу:**
   ```
   Command: /home/your-username/your-project/deploy.sh
   Schedule: Every hour  # или по вашему графику
   Description: Auto-deploy bot
   ```

### **Способ 2: Webhook (GitHub → PythonAnywhere)**

1. **Создайте API endpoint на PythonAnywhere:**
   ```python
   # webhooks.py
   from flask import Flask, request
   import subprocess
   import os

   app = Flask(__name__)

   @app.route('/webhook', methods=['POST'])
   def webhook():
       if request.method == 'POST':
           # Проверяем секрет (опционально)
           # secret = request.headers.get('X-Hub-Signature-256')

           # Запускаем деплой
           result = subprocess.run(['/home/your-username/your-project/deploy.sh'],
                                 capture_output=True, text=True)

           return f"Deploy result: {result.stdout}", 200
       return "Method not allowed", 405

   if __name__ == '__main__':
       app.run(host='0.0.0.0', port=8080)
   ```

2. **Запустите webhook сервер:**
   ```bash
   nohup python webhooks.py > webhook.log 2>&1 &
   ```

3. **Настройте webhook в GitHub:**
   - Repository → Settings → Webhooks → Add webhook
   - Payload URL: `https://your-username.pythonanywhere.com/webhook`
   - Content type: `application/json`
   - Events: `push` (только main ветка)

### **Способ 3: Always-on Task**

1. **В PythonAnywhere Dashboard → Tasks → Always-on**
2. **Добавьте задачу:**
   ```bash
   python main.py
   ```
3. **Для обновлений используйте cron job:**
   ```bash
   # В crontab
   */30 * * * * /home/your-username/your-project/deploy.sh
   ```

### **Способ 4: PythonAnywhere API (продвинутый)**

Используйте `pythonanywhere_api_deploy.py` для полного контроля через REST API:

```bash
# Запустите интерактивный скрипт
python pythonanywhere_api_deploy.py
```

**Возможности API:**
- 🚀 Ручной деплой через API
- 📅 Создание/управление cron jobs
- 🔄 Управление always-on задачами
- 📺 Выполнение команд в консоли
- 🌐 Перезагрузка веб-приложений

**Настройка:**
1. Получите API токен: Account → API Token
2. Измените настройки в `pythonanywhere_api_deploy.py`
3. Запустите скрипт

## 🔧 Ручной деплой

Если нужно обновить бота вручную:

```bash
# В консоли PythonAnywhere
cd /home/your-username/your-project
./deploy.sh
```

## 📊 Мониторинг

### **Проверка статуса бота:**
```bash
ps aux | grep python
tail -f bot.log
```

### **Проверка webhook логов:**
```bash
tail -f webhook.log
```

## ⚠️ Важные замечания

- **Тестируйте скрипт локально** перед настройкой автоматизации
- **Добавьте логирование** в скрипт деплоя для отладки
- **Настройте уведомления** о неудачных деплоях
- **Делайте бэкапы** базы данных перед каждым деплоем

## 🎯 Рекомендации

1. **Используйте cron job** каждые 30-60 минут для регулярных обновлений
2. **Добавьте проверку здоровья** в скрипт деплоя
3. **Настройте email уведомления** при ошибках
4. **Тестируйте** на staging окружении перед продакшеном

## 🔍 Устранение неполадок

### **Бот не перезапускается:**
```bash
# Проверьте процессы
ps aux | grep python

# Убейте все процессы бота
pkill -f "python.*main.py"

# Запустите заново
python main.py
```

### **Git pull не работает:**
```bash
# Проверьте статус
git status
git log --oneline -5

# Принудительно обновите
git reset --hard origin/main
git pull origin main --force
```
