import { NextResponse } from 'next/server';
import { TelegramBot } from '../../../lib/telegram';

export const dynamic = 'force-dynamic';
export const runtime = 'nodejs';

async function setupWebhook() {
  const baseUrl = process.env.NEXT_PUBLIC_APP_URL;
  if (!baseUrl) {
    throw new Error('NEXT_PUBLIC_APP_URL not configured');
  }

  const webhookUrl = `${baseUrl}/api/webhook`;
  const secretToken = process.env.WEBHOOK_SECRET;

  console.log('Setting webhook to:', webhookUrl);

  return await TelegramBot.setWebhook(webhookUrl, {
    secret_token: secretToken,
  });
}

export async function GET() {
  try {
    const result = await setupWebhook();
    return NextResponse.json({
      success: true,
      result,
    });
  } catch (error: any) {
    console.error('Setup webhook error:', error);
    return NextResponse.json({ error: error.message || 'Failed to setup webhook' }, { status: 500 });
  }
}

export async function POST() {
  try {
    const result = await setupWebhook();
    return NextResponse.json({
      success: true,
      result,
    });
  } catch (error: any) {
    console.error('Setup webhook error:', error);
    return NextResponse.json({ error: error.message || 'Failed to setup webhook' }, { status: 500 });
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
