import { getPrismaClient } from '@/lib/prisma';
import { BotManager } from './bot-manager';

const DEFAULT_MESSAGES = {
  main_menu: {
    title: "🎉 Добро пожаловать в бот психолога Сауле Сайфуллиной!",
    text: (
      "Я помогу вам:\n" +
      "• Перейти в Сообщество 5-го потока Квеста \"Денежный прорыв\"\n" +
      "• Купить запись 2-го потока квеста \"Денежный прорыв\"\n" +
      "• Записаться на консультацию\n" +
      "• Получить полезный контент\n\n" +
      "Выберите нужное действие:"
    ),
    parse_mode: "HTML",
    is_main_menu: true,
    buttons: [
      { text: "📢 Открытый канал «Про деньги»", type: "callback", action: "tg_channel", row: 0, order: 0 },
      { text: "🎯 Бесплатный Квест 'Денежный прорыв'", type: "callback", action: "quest_community", row: 1, order: 0 },
      { text: "🧪 Пройти тест", type: "url", action: "https://t.me/saule_prodengi", row: 2, order: 0 },
      { text: "🧘‍♀️ Забрать практику", type: "url", action: "https://t.me/saule_prodengi", row: 3, order: 0 },
      { text: "🚀 Доступ в клуб «Квантовый скачок»", type: "callback", action: "closed_club", row: 4, order: 0 },
      { text: "💰 Купить Курс 'Деньги в радости'", type: "callback", action: "course_buy", row: 5, order: 0 },
      { text: "🎬 Купить запись 2-го потока Квеста", type: "callback", action: "buy_quest", row: 6, order: 0 },
      { text: "💬 Консультация", type: "callback", action: "consultation", row: 7, order: 0 },

      { text: "ℹ️ О боте", type: "callback", action: "about", row: 9, order: 0 },
    ],
  },
};

export async function seedDatabase() {
  console.log('🌱 Seeding database...');

  const { getPrismaClient } = await import('@/lib/prisma');
  const prisma = getPrismaClient();

  if (!prisma) {
    console.warn('Prisma not available during build, skipping seed');
    return;
  }

  // Создаем дефолтные сообщения
  for (const [pageKey, messageData] of Object.entries(DEFAULT_MESSAGES)) {
    const existingMessage = await BotManager.getMessageByKey(pageKey);

    if (!existingMessage) {
      console.log(`Creating message: ${pageKey}`);
      const message = await BotManager.createMessage({
        page_key: pageKey,
        title: messageData.title,
        text: messageData.text,
        parse_mode: messageData.parse_mode,
        is_main_menu: messageData.is_main_menu,
      });

      // Создаем кнопки для сообщения
      for (const buttonData of messageData.buttons) {
        await BotManager.createButton({
          message_id: message.id,
          text: buttonData.text,
          button_type: buttonData.type,
          action_data: buttonData.action,
          row: buttonData.row,
          order: buttonData.order,
        });
      }
    } else {
      console.log(`Message ${pageKey} already exists`);
    }
  }

  console.log('✅ Database seeded successfully');
}
