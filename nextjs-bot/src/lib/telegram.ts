import { TelegramInlineKeyboardMarkup } from '../types/telegram';

const BOT_TOKEN = process.env.BOT_TOKEN!;
const BASE_URL = `https://api.telegram.org/bot${BOT_TOKEN}`;

export class TelegramBot {
  static async sendMessage(
    chatId: number | string,
    text: string,
    options: {
      parse_mode?: 'HTML' | 'Markdown';
      reply_markup?: TelegramInlineKeyboardMarkup;
      disable_web_page_preview?: boolean;
    } = {}
  ) {
    const response = await fetch(`${BASE_URL}/sendMessage`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        chat_id: chatId,
        text,
        ...options,
      }),
    });

    if (!response.ok) {
      throw new Error(`Telegram API error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  static async editMessageText(
    chatId: number | string,
    messageId: number,
    text: string,
    options: {
      parse_mode?: 'HTML' | 'Markdown';
      reply_markup?: TelegramInlineKeyboardMarkup;
      disable_web_page_preview?: boolean;
    } = {}
  ) {
    const response = await fetch(`${BASE_URL}/editMessageText`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        chat_id: chatId,
        message_id: messageId,
        text,
        ...options,
      }),
    });

    if (!response.ok) {
      throw new Error(`Telegram API error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  static async answerCallbackQuery(
    callbackQueryId: string,
    options: {
      text?: string;
      show_alert?: boolean;
      url?: string;
      cache_time?: number;
    } = {}
  ) {
    const response = await fetch(`${BASE_URL}/answerCallbackQuery`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        callback_query_id: callbackQueryId,
        ...options,
      }),
    });

    if (!response.ok) {
      throw new Error(`Telegram API error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  static async setWebhook(url: string, options: { secret_token?: string } = {}) {
    const response = await fetch(`${BASE_URL}/setWebhook`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        url,
        ...options,
      }),
    });

    if (!response.ok) {
      throw new Error(`Telegram API error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  static async deleteWebhook() {
    const response = await fetch(`${BASE_URL}/deleteWebhook`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({}),
    });

    if (!response.ok) {
      throw new Error(`Telegram API error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }
}
