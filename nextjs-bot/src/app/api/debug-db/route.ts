
import { NextResponse } from 'next/server';
import { BotManager } from '../../../utils/bot-manager';

export const dynamic = 'force-dynamic';

export async function GET() {
    try {
        const messages = await BotManager.getAllMessages();
        const detailed = messages.map(m => ({
            id: m.id,
            key: m.page_key,
            key_len: m.page_key.length,
            title: m.title
        }));

        return NextResponse.json({
            success: true,
            count: messages.length,
            messages: detailed
        });
    } catch (error) {
        return NextResponse.json({ success: false, error: 'Failed to fetch messages' }, { status: 500 });
    }
}
