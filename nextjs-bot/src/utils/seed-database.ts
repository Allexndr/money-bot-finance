import { getPrismaClient } from '../lib/prisma';
import { BotManager } from './bot-manager';

const DEFAULT_MESSAGES = {
  main_menu: {
    title: "🎉 Бот психолога Сауле Сайфуллиной",
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
  consultation: {
    title: "💬 Консультация",
    text: "Чтобы записаться на консультацию, напишите мне в личные сообщения: @Saule_Saifullina\n\nЯ отвечу на все ваши вопросы и мы подберем удобное время.",
    parse_mode: "HTML",
    is_main_menu: false,
    buttons: [
      { text: "🔙 Назад", type: "callback", action: "main_menu", row: 0, order: 0 }
    ]
  },
  about: {
    title: "ℹ️ О боте",
    text: "Этот бот создан, чтобы помочь вам проработать финансовые блоки и выйти на новый уровень дохода.\n\nЗдесь вы найдете:\n- Бесплатные практики\n- Информацию о курсах\n- Возможность записаться на консультацию",
    parse_mode: "HTML",
    is_main_menu: false,
    buttons: [
      { text: "🔙 Назад", type: "callback", action: "main_menu", row: 0, order: 0 }
    ]
  },
  course_buy: {
    title: "💰 Курс 'Деньги в радости'",
    text: "Курс 'Деньги в радости' — это глубокая проработка ваших отношений с финансами.\n\nПодробности и программа курса доступны по ссылке ниже.",
    parse_mode: "HTML",
    is_main_menu: false,
    buttons: [
      { text: "🔗 Подробнее о курсе", type: "url", action: "https://t.me/saule_prodengi", row: 0, order: 0 },
      { text: "🔙 Назад", type: "callback", action: "main_menu", row: 1, order: 0 }
    ]
  },
  buy_quest: {
    title: "🎬 Запись 2-го потока Квеста",
    text: "Вы можете приобрести запись 2-го потока квеста 'Денежный прорыв'.\n\nЭто отличная возможность пройти квест в своем темпе.",
    parse_mode: "HTML",
    is_main_menu: false,
    buttons: [
      { text: "💳 Купить (Ссылка)", type: "url", action: "https://t.me/saule_prodengi", row: 0, order: 0 },
      { text: "🔙 Назад", type: "callback", action: "main_menu", row: 1, order: 0 }
    ]
  },
  closed_club: {
    title: "🚀 Клуб «Квантовый скачок»",
    text: "Закрытый клуб для тех, кто хочет расти постоянно.\n\nВступайте в клуб, чтобы быть в окружении единомышленников.",
    parse_mode: "HTML",
    is_main_menu: false,
    buttons: [
      { text: "🚪 Вступить в клуб", type: "url", action: "https://t.me/saule_prodengi", row: 0, order: 0 },
      { text: "🔙 Назад", type: "callback", action: "main_menu", row: 1, order: 0 }
    ]
  },
  quest_community: {
    title: "🎯 Квест 'Денежный прорыв'",
    text: "Присоединяйтесь к бесплатному квесту и начните свой путь к финансовой свободе прямо сейчас!",
    parse_mode: "HTML",
    is_main_menu: false,
    buttons: [
      { text: "👉 Перейти к квесту", type: "url", action: "https://t.me/saule_prodengi", row: 0, order: 0 },
      { text: "🔙 Назад", type: "callback", action: "main_menu", row: 1, order: 0 }
    ]
  },
  tg_channel: {
    title: "📢 Канал «Про деньги»",
    text: "Подписывайтесь на мой открытый канал, там много полезного!",
    parse_mode: "HTML",
    is_main_menu: false,
    buttons: [
      { text: "🔗 Перейти в канал", type: "url", action: "https://t.me/saule_prodengi", row: 0, order: 0 },
      { text: "🔙 Назад", type: "callback", action: "main_menu", row: 1, order: 0 }
    ]
  }
};

export async function seedDatabase(): Promise<string[]> {
  const logs: string[] = [];
  logs.push('🌱 Seeding database...');

  const prisma = getPrismaClient();

  if (!prisma) {
    logs.push('Prisma not available during build, skipping seed');
    return logs;
  }

  // Создаем дефолтные сообщения
  for (const [pageKey, messageData] of Object.entries(DEFAULT_MESSAGES)) {
    const existingMessage = await BotManager.getMessageByKey(pageKey);
    let messageId: string;

    if (!existingMessage) {
      logs.push(`Creating message: ${pageKey}`);
      try {
        const message = await BotManager.createMessage({
          page_key: pageKey,
          title: messageData.title,
          text: messageData.text,
          parse_mode: messageData.parse_mode,
          is_main_menu: messageData.is_main_menu,
        });
        messageId = message.id;
        logs.push(`Created message ${pageKey} with ID ${messageId}`);
      } catch (e: any) {
        logs.push(`Error creating message ${pageKey}: ${e.message}`);
        continue;
      }
    } else {
      logs.push(`Updating existing message: ${pageKey}`);
      messageId = existingMessage.id;

      // Update message content
      await BotManager.updateMessage(messageId, {
        title: messageData.title,
        text: messageData.text,
        parse_mode: messageData.parse_mode,
        is_main_menu: messageData.is_main_menu,
      });

      // Clear existing buttons to recreate them consistently
      const currentButtons = await BotManager.getButtonsForMessage(messageId);
      for (const btn of currentButtons) {
        await BotManager.deleteButton(btn.id);
      }
    }

    // Создаем кнопки для сообщения (ALWAYS recreate/create keys)
    for (const buttonData of messageData.buttons) {
      try {
        await BotManager.createButton({
          message_id: messageId,
          text: buttonData.text,
          button_type: buttonData.type,
          action_data: buttonData.action,
          row: buttonData.row,
          order: buttonData.order,
        });
      } catch (e: any) {
        logs.push(`Error creating button for ${pageKey}: ${e.message}`);
      }
    }
  }

  // CLEANUP: Удаляем demo_access если существует (для очистки продакшн базы)
  try {
    const demoMsg = await BotManager.getMessageByKey('demo_access');
    if (demoMsg) {
      logs.push('🧹 Cleanup: Found ' + demoMsg.id + ' demo_access message, deleting...');
      // Сначала удаляем кнопки
      const buttons = await BotManager.getButtonsForMessage(demoMsg.id);
      for (const btn of buttons) {
        await BotManager.deleteButton(btn.id);
      }
      // Удаляем сообщение
      await BotManager.deleteMessage(demoMsg.id);
      logs.push('✅ Cleanup: demo_access deleted.');
    }
  } catch (e: any) {
    logs.push(`Cleanup error: ${e.message}`);
  }

  logs.push('✅ Database seeded successfully');
  return logs;
}
