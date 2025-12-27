import { NextRequest, NextResponse } from 'next/server';
import { TelegramUpdate, TelegramCallbackQuery, TelegramMessage } from '@/types/telegram';
import { TelegramBot } from '@/lib/telegram';

const WEBHOOK_SECRET = process.env.WEBHOOK_SECRET;

export const dynamic = 'force-dynamic';
export const runtime = 'nodejs';

// Навигационная история пользователей
const USER_NAVIGATION_HISTORY: { [key: number]: string[] } = {};

function addToHistory(userId: number, pageKey: string) {
  if (!USER_NAVIGATION_HISTORY[userId]) {
    USER_NAVIGATION_HISTORY[userId] = [];
  }

  // Убираем дубликаты и ограничиваем историю
  USER_NAVIGATION_HISTORY[userId] = USER_NAVIGATION_HISTORY[userId]
    .filter(key => key !== pageKey)
    .slice(-10);
  USER_NAVIGATION_HISTORY[userId].push(pageKey);
}

function getPreviousPage(userId: number): string | null {
  const history = USER_NAVIGATION_HISTORY[userId];
  if (!history || history.length < 2) return null;
  return history[history.length - 2];
}

async function handleStartCommand(chatId: number, user: any) {
  const { getPrismaClient } = await import('@/lib/prisma');
  const { BotManager } = await import('@/utils/bot-manager');

  const prisma = getPrismaClient();
  if (prisma) {
    // Создаем или обновляем пользователя
    await prisma.user.upsert({
      where: { telegram_id: user.id },
      update: {
        username: user.username,
        first_name: user.first_name,
        last_name: user.last_name,
      },
      create: {
        telegram_id: user.id,
        username: user.username,
        first_name: user.first_name,
        last_name: user.last_name,
      },
    });
  }

  // Получаем главное меню
  const mainMenu = await BotManager.getMessageByKey('main_menu');

  if (mainMenu) {
    addToHistory(user.id, 'main_menu');
    const keyboard = await BotManager.buildKeyboardFromDb(mainMenu.id, user.id);
    const text = mainMenu.title ? `${mainMenu.title}\n\n${mainMenu.text}` : mainMenu.text;

    await TelegramBot.sendMessage(chatId, text, {
      parse_mode: mainMenu.parse_mode as 'HTML' | 'Markdown',
      reply_markup: keyboard,
    });
  } else {
    await TelegramBot.sendMessage(chatId, 'Добро пожаловать! Бот находится в разработке.');
  }
}

async function handleCallbackQuery(callbackQuery: TelegramCallbackQuery) {
  const { id: queryId, from: user, data } = callbackQuery;
  const chatId = callbackQuery.message?.chat.id;

  if (!chatId || !data) return;

  // Отвечаем на callback query (чтобы часики не висели) - handled inside AdminManager for admin events, but generally good here unless AdminManager handles it better.
  // AdminManager answers it if it's admin.

  if (data.startsWith('admin_')) {
    const { AdminManager } = await import('@/utils/admin-manager');
    await AdminManager.handleAdminCallback(callbackQuery);
    return;
  }

  await TelegramBot.answerCallbackQuery(queryId);

  // Проверяем, есть ли сообщение в базе данных с таким page_key
  const { BotManager } = await import('@/utils/bot-manager');
  const dbMessage = await BotManager.getMessageByKey(data);

  if (dbMessage) {
    // Это переход на сообщение из базы данных
    addToHistory(user.id, data);
    await showMessageFromDb(callbackQuery, dbMessage, user.id);
    return;
  }

  // Обработка других callback данных
  if (data === 'back') {
    const previousPage = getPreviousPage(user.id);
    if (previousPage) {
      const prevMessage = await BotManager.getMessageByKey(previousPage);
      if (prevMessage) {
        await showMessageFromDb(callbackQuery, prevMessage, user.id);
      }
    }
  }
}

async function showMessageFromDb(callbackQuery: TelegramCallbackQuery, message: any, userId: number) {
  const chatId = callbackQuery.message?.chat.id;
  const messageId = callbackQuery.message?.message_id;

  if (!chatId || !messageId) return;

  const { BotManager } = await import('@/utils/bot-manager');
  const keyboard = await BotManager.buildKeyboardFromDb(message.id, userId);
  const text = message.title ? `${message.title}\n\n${message.text}` : message.text;

  await TelegramBot.editMessageText(chatId, messageId, text, {
    parse_mode: message.parse_mode as 'HTML' | 'Markdown',
    reply_markup: keyboard,
  });
}

async function handleMessage(message: TelegramMessage) {
  const chatId = message.chat.id;
  const user = message.from;

  if (!user) return;

  const text = message.text;
  if (!text) return;

  // Обработка команд
  if (text.startsWith('/start')) {
    await handleStartCommand(chatId, user);
  } else if (text.startsWith('/admin')) {
    const { AdminManager } = await import('@/utils/admin-manager');
    await AdminManager.handleAdminCommand(chatId, user.id);
  } else if (text.startsWith('/help')) {
    await TelegramBot.sendMessage(chatId, 'Это бот для управления финансами. Используйте /start для начала.');
  } else {
    // Check for Admin State Input
    const { AdminManager } = await import('@/utils/admin-manager');
    const handled = await AdminManager.handleUserInput(chatId, user.id, text);
    if (!handled) {
      // Default echo or ignore?
      // await TelegramBot.sendMessage(chatId, `Вы написали: ${text}`);
    }
  }
}

export async function POST(request: NextRequest) {
  try {
    // Проверка секрета вебхука
    const secret = request.headers.get('x-telegram-bot-api-secret-token');
    if (WEBHOOK_SECRET && secret !== WEBHOOK_SECRET) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const update: TelegramUpdate = await request.json();

    // Обработка обновлений
    if (update.message) {
      await handleMessage(update.message);
    } else if (update.callback_query) {
      await handleCallbackQuery(update.callback_query);
    }

    return NextResponse.json({ ok: true });
  } catch (error) {
    console.error('Webhook error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}

export async function GET() {
  return NextResponse.json({ status: 'Bot webhook is active' });
}
