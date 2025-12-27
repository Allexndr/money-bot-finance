import { getPrismaClient } from '@/lib/prisma';
import { TelegramInlineKeyboardButton, TelegramInlineKeyboardMarkup } from '@/types/telegram';

export interface BotMessage {
  id: number;
  page_key: string;
  title?: string;
  text: string;
  parse_mode: string;
  is_main_menu: boolean;
  created_at: Date;
  updated_at: Date;
}

export interface BotButton {
  id: number;
  message_id: number;
  text: string;
  button_type: string; // 'callback', 'url', 'message'
  action_data: string;
  row: number;
  order: number;
  is_active: boolean;
  created_at: Date;
  updated_at: Date;
}

export class BotManager {
  static async getMessageByKey(pageKey: string): Promise<BotMessage | null> {
    const prisma = getPrismaClient();
    if (!prisma) return null;
    return prisma.botMessage.findUnique({
      where: { page_key: pageKey },
    });
  }

  static async getButtonsForMessage(messageId: number): Promise<BotButton[]> {
    const prisma = getPrismaClient();
    if (!prisma) return [];
    return prisma.botButton.findMany({
      where: {
        message_id: messageId,
        is_active: true,
      },
      orderBy: [
        { row: 'asc' },
        { order: 'asc' },
      ],
    });
  }

  static async buildKeyboardFromDb(
    messageId: number,
    userId?: number,
    callbackPrefix: string = "nav",
    addBackButton: boolean = true
  ): Promise<TelegramInlineKeyboardMarkup> {
    const buttons = await this.getButtonsForMessage(messageId);

    if (!buttons.length) {
      return { inline_keyboard: [] };
    }

    // Группируем кнопки по строкам
    const keyboardRows: { [key: number]: BotButton[] } = {};
    buttons.forEach(button => {
      if (!keyboardRows[button.row]) {
        keyboardRows[button.row] = [];
      }
      keyboardRows[button.row].push(button);
    });

    // Сортируем строки и создаем клавиатуру
    const sortedRows = Object.keys(keyboardRows).map(Number).sort();
    const keyboard: TelegramInlineKeyboardButton[][] = [];

    sortedRows.forEach(row => {
      const rowButtons = keyboardRows[row].sort((a, b) => a.order - b.order);
      const inlineButtons: TelegramInlineKeyboardButton[] = [];

      rowButtons.forEach(button => {
        let inlineButton: TelegramInlineKeyboardButton;

        switch (button.button_type) {
          case 'callback':
            inlineButton = {
              text: button.text,
              callback_data: button.action_data,
            };
            break;
          case 'url':
            inlineButton = {
              text: button.text,
              url: button.action_data,
            };
            break;
          case 'message':
            inlineButton = {
              text: button.text,
              callback_data: button.action_data,
            };
            break;
          default:
            inlineButton = {
              text: button.text,
              callback_data: button.action_data,
            };
        }

        inlineButtons.push(inlineButton);
      });

      if (inlineButtons.length > 0) {
        keyboard.push(inlineButtons);
      }
    });

    return { inline_keyboard: keyboard };
  }

  static async createMessage(data: {
    page_key: string;
    title?: string;
    text: string;
    parse_mode?: string;
    is_main_menu?: boolean;
  }): Promise<BotMessage> {
    const prisma = getPrismaClient();
    if (!prisma) throw new Error('Database not available');
    return prisma.botMessage.create({
      data: {
        page_key: data.page_key,
        title: data.title,
        text: data.text,
        parse_mode: data.parse_mode || 'HTML',
        is_main_menu: data.is_main_menu || false,
      },
    });
  }

  static async updateMessage(
    id: number,
    data: Partial<{
      page_key: string;
      title: string | null;
      text: string;
      parse_mode: string;
      is_main_menu: boolean;
    }>
  ): Promise<BotMessage> {
    const prisma = getPrismaClient();
    if (!prisma) throw new Error('Database not available');
    return prisma.botMessage.update({
      where: { id },
      data,
    });
  }

  static async deleteMessage(id: number): Promise<BotMessage> {
    const prisma = getPrismaClient();
    if (!prisma) throw new Error('Database not available');
    return prisma.botMessage.delete({
      where: { id },
    });
  }

  static async createButton(data: {
    message_id: number;
    text: string;
    button_type: string;
    action_data: string;
    row?: number;
    order?: number;
  }): Promise<BotButton> {
    const prisma = getPrismaClient();
    if (!prisma) throw new Error('Database not available');
    return prisma.botButton.create({
      data: {
        message_id: data.message_id,
        text: data.text,
        button_type: data.button_type,
        action_data: data.action_data,
        row: data.row || 0,
        order: data.order || 0,
      },
    });
  }

  static async updateButton(
    id: number,
    data: Partial<{
      text: string;
      button_type: string;
      action_data: string;
      row: number;
      order: number;
      is_active: boolean;
    }>
  ): Promise<BotButton> {
    const prisma = getPrismaClient();
    if (!prisma) throw new Error('Database not available');
    return prisma.botButton.update({
      where: { id },
      data,
    });
  }

  static async deleteButton(id: number): Promise<BotButton> {
    const prisma = getPrismaClient();
    if (!prisma) throw new Error('Database not available');
    return prisma.botButton.delete({
      where: { id },
    });
  }

  static async getAllMessages(): Promise<BotMessage[]> {
    const prisma = getPrismaClient();
    if (!prisma) return [];
    return prisma.botMessage.findMany({
      orderBy: { created_at: 'desc' },
    });
  }

  static async getAllButtons(): Promise<BotButton[]> {
    const prisma = getPrismaClient();
    if (!prisma) return [];
    return prisma.botButton.findMany({
      include: { message: true },
      orderBy: { created_at: 'desc' },
    });
  }
}
