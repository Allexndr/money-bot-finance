import { NextRequest, NextResponse } from 'next/server';

// Настройки бота
const BOT_TOKEN = process.env.BOT_TOKEN!;
const CHAT_ID = process.env.ADMIN_CHAT_ID || '5450018125'; // ID админа для уведомлений

// Функция для отправки сообщения в Telegram
async function sendTelegramMessage(text: string) {
  try {
    const response = await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        chat_id: CHAT_ID,
        text: text,
        parse_mode: 'HTML',
      }),
    });

    return response.ok;
  } catch (error) {
    console.error('Error sending Telegram message:', error);
    return false;
  }
}

export async function POST(request: NextRequest) {
  try {
    // Получаем данные webhook от GitHub
    const body = await request.text();
    const signature = request.headers.get('x-hub-signature-256');
    const event = request.headers.get('x-github-event');

    console.log('Webhook received:', event);

    // Проверяем, что это push событие
    if (event === 'push') {
      const data = JSON.parse(body);
      const repo = data.repository?.name;
      const branch = data.ref?.replace('refs/heads/', '');
      const commits = data.commits || [];

      // Формируем сообщение для бота
      let message = `🚀 <b>GitHub Update</b>\n\n`;
      message += `📦 <b>Repository:</b> ${repo}\n`;
      message += `🌿 <b>Branch:</b> ${branch}\n`;
      message += `📝 <b>Commits:</b> ${commits.length}\n\n`;

      if (commits.length > 0) {
        message += `📋 <b>Changes:</b>\n`;
        commits.slice(0, 3).forEach((commit: any, index: number) => {
          const shortHash = commit.id.substring(0, 7);
          const shortMessage = commit.message.split('\n')[0].substring(0, 50);
          message += `${index + 1}. <code>${shortHash}</code> - ${shortMessage}\n`;
        });

        if (commits.length > 3) {
          message += `... and ${commits.length - 3} more\n`;
        }
      }

      message += `\n🔄 <b>Auto-deploy in progress...</b>`;

      // Отправляем сообщение в Telegram
      const sent = await sendTelegramMessage(message);
      if (sent) {
        console.log('✅ Notification sent to Telegram bot');
      } else {
        console.error('❌ Failed to send notification to Telegram');
      }
    }

    return NextResponse.json({ status: 'ok' });
  } catch (error) {
    console.error('Webhook error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}

export async function GET() {
  return NextResponse.json({
    status: 'Webhook service is running',
    timestamp: new Date().toISOString()
  });
}
