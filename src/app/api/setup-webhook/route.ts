import { NextResponse } from 'next/server';
import { TelegramBot } from '@/lib/telegram';

export async function POST() {
  try {
    const baseUrl = process.env.NEXT_PUBLIC_APP_URL;
    if (!baseUrl) {
      return NextResponse.json({ error: 'NEXT_PUBLIC_APP_URL not configured' }, { status: 500 });
    }

    const webhookUrl = `${baseUrl}/api/webhook`;
    const secretToken = process.env.WEBHOOK_SECRET;

    console.log('Setting webhook to:', webhookUrl);

    const result = await TelegramBot.setWebhook(webhookUrl, {
      secret_token: secretToken,
    });

    return NextResponse.json({
      success: true,
      webhook_url: webhookUrl,
      result,
    });
  } catch (error) {
    console.error('Setup webhook error:', error);
    return NextResponse.json({ error: 'Failed to setup webhook' }, { status: 500 });
  }
}

export async function DELETE() {
  try {
    const result = await TelegramBot.deleteWebhook();
    return NextResponse.json({
      success: true,
      result,
    });
  } catch (error) {
    console.error('Delete webhook error:', error);
    return NextResponse.json({ error: 'Failed to delete webhook' }, { status: 500 });
  }
}
