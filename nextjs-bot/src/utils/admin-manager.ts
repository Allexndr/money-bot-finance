import { TelegramBot } from '../lib/telegram';
import { BotManager } from './bot-manager';
import { getPrismaClient } from '../lib/prisma';
import { TelegramCallbackQuery, TelegramMessage, TelegramInlineKeyboardButton, TelegramInlineKeyboardMarkup } from '../types/telegram';

const ADMIN_IDS = [5450018125, 235639622, 6682947818]; // Add IDs here

// State Machine Constants
const ACTIONS = {
    CREATE_BUTTON: 'create_button',
    EDIT_MESSAGE_TEXT: 'edit_message_text',
    EDIT_MESSAGE_TITLE: 'edit_message_title',
};

const STEPS = {
    INITIAL_TYPE_SELECTION: 'initial_type_selection',
    TEXT_INPUT: 'text_input',
    URL_INPUT: 'url_input',
    PAGE_SELECT: 'page_select',
};

export class AdminManager {

    static isAdmin(userId: number): boolean {
        return ADMIN_IDS.includes(userId);
    }

    static async clearState(userId: number) {
        const prisma = getPrismaClient();
        if (!prisma) return;
        await prisma.botState.deleteMany({ where: { telegram_id: userId } });
    }

    static async setState(userId: number, action: string, step: string, data: any = {}) {
        const prisma = getPrismaClient();
        if (!prisma) return;

        await prisma.botState.upsert({
            where: { telegram_id: userId },
            update: { action, step, data: JSON.stringify(data) },
            create: { telegram_id: userId, action, step, data: JSON.stringify(data) },
        });
    }

    static async getState(userId: number) {
        const prisma = getPrismaClient();
        if (!prisma) return null;
        return prisma.botState.findUnique({ where: { telegram_id: userId } });
    }

    static async handleAdminCommand(chatId: number, userId: number) {
        if (!this.isAdmin(userId)) return;

        await this.clearState(userId);

        const buttons: TelegramInlineKeyboardButton[][] = [
            [{ text: "🔘 Управление кнопками", callback_data: "admin_button_management" }],
            [{ text: "🏠 Главное меню", callback_data: "admin_open_main_menu" }]
        ];

        await TelegramBot.sendMessage(chatId, "🔧 <b>АДМИН-ПАНЕЛЬ</b>\n\nВыберите действие:", {
            parse_mode: 'HTML',
            reply_markup: { inline_keyboard: buttons }
        });
    }

    static async handleAdminCallback(query: TelegramCallbackQuery) {
        const userId = query.from.id;
        const chatId = query.message?.chat.id;
        const messageId = query.message?.message_id;
        const data = query.data;

        if (!chatId || !messageId || !data || !this.isAdmin(userId)) return;

        await TelegramBot.answerCallbackQuery(query.id);

        if (data === 'admin_panel') {
            await this.clearState(userId);
            const buttons: TelegramInlineKeyboardButton[][] = [
                [{ text: "🔘 Управление кнопками", callback_data: "admin_button_management" }],
                [{ text: "🏠 Главное меню", callback_data: "admin_open_main_menu" }]
            ];
            await TelegramBot.editMessageText(chatId, messageId, "🔧 <b>АДМИН-ПАНЕЛЬ</b>\n\nВыберите действие:", {
                parse_mode: 'HTML',
                reply_markup: { inline_keyboard: buttons }
            });
            return;
        }

        if (data === 'admin_button_management') {
            await this.showButtonManagement(chatId, messageId);
            return;
        }

        if (data.startsWith('admin_edit_message_')) {
            // admin_edit_message_{id}
            const msgId = data.split('_').pop() || '';
            await this.showEditMessage(chatId, messageId, msgId);
            return;
        }

        // Create Button Flow
        if (data.startsWith('admin_create_button_msg_')) {
            const msgId = data.split('_').pop() || '';

            await this.setState(userId, ACTIONS.CREATE_BUTTON, STEPS.INITIAL_TYPE_SELECTION, { message_id: msgId });

            const text = "➕ <b>ДОБАВЛЕНИЕ КНОПКИ</b>\n\n<b>Куда должна вести эта кнопка?</b>\n\n";
            const buttons: TelegramInlineKeyboardButton[][] = [
                [
                    { text: "🔗 Ссылка на сайт", callback_data: `admin_btn_creation_type_url_${msgId}` },
                    { text: "📄 Другая страница", callback_data: `admin_btn_creation_type_message_${msgId}` }
                ],
                [
                    { text: "🔙 Отмена", callback_data: `admin_edit_message_${msgId}` }
                ]
            ];

            await TelegramBot.editMessageText(chatId, messageId, text, {
                parse_mode: 'HTML',
                reply_markup: { inline_keyboard: buttons }
            });
            return;
        }

        if (data.startsWith('admin_btn_creation_type_')) {
            const parts = data.split('_');
            const msgId = parts.pop() || '';
            const type = parts.pop(); // 'url' or 'message'

            const state = await this.getState(userId);
            if (state && state.action === ACTIONS.CREATE_BUTTON) {
                const stateData = JSON.parse(state.data);
                stateData.button_type = type;

                if (type === 'url') {
                    await this.setState(userId, ACTIONS.CREATE_BUTTON, STEPS.URL_INPUT, stateData);
                    await TelegramBot.editMessageText(chatId, messageId,
                        "🔗 <b>Отправьте ссылку</b>\n\nПросто пришлите ссылку, которая должна открываться при нажатии.\n<i>Обязательно с https:// (например: https://yandex.ru)</i>",
                        {
                            parse_mode: 'HTML',
                            reply_markup: { inline_keyboard: [[{ text: "🔙 Отмена", callback_data: `admin_create_button_msg_${msgId}` }]] }
                        }
                    );
                } else if (type === 'message') {
                    await this.setState(userId, ACTIONS.CREATE_BUTTON, STEPS.PAGE_SELECT, stateData);

                    // Show pages
                    const messages = await BotManager.getAllMessages();
                    const pageButtons: TelegramInlineKeyboardButton[][] = [];
                    messages.forEach(msg => {
                        pageButtons.push([{
                            text: `📄 ${msg.title || msg.page_key}`,
                            callback_data: `admin_create_btn_select_page_${msgId}_${msg.page_key}`
                        }]);
                    });
                    pageButtons.push([{ text: "🔙 Отмена", callback_data: `admin_create_button_msg_${msgId}` }]);

                    await TelegramBot.editMessageText(chatId, messageId,
                        "📄 <b>Куда должна вести кнопка?</b>\n\nВыберите страницу из списка ниже:",
                        {
                            parse_mode: 'HTML',
                            reply_markup: { inline_keyboard: pageButtons }
                        }
                    );
                }
            }
            return;
        }

        if (data.startsWith('admin_create_btn_select_page_')) {
            // admin_create_btn_select_page_{msgId}_{pageKey}
            const parts = data.split('_');
            const pageKey = parts.pop();
            const msgId = parts.pop() || '';

            const state = await this.getState(userId);
            if (state) {
                const stateData = JSON.parse(state.data);
                stateData.target_page_key = pageKey;

                await this.setState(userId, ACTIONS.CREATE_BUTTON, STEPS.TEXT_INPUT, stateData);

                await TelegramBot.editMessageText(chatId, messageId,
                    `✅ Выбрана страница: <b>${pageKey}</b>\n\nТеперь <b>напишите текст кнопки</b> (то, что будет на ней написано).`,
                    {
                        parse_mode: 'HTML',
                        reply_markup: { inline_keyboard: [[{ text: "🔙 Отмена", callback_data: `admin_create_button_msg_${msgId}` }]] }
                    }
                );
            }
            return;
        }
    }

    static async handleUserInput(chatId: number, userId: number, text: string) {
        if (!this.isAdmin(userId)) return false;

        const state = await this.getState(userId);
        if (!state) return false;

        const stateData = JSON.parse(state.data);

        if (state.action === ACTIONS.CREATE_BUTTON) {
            if (state.step === STEPS.URL_INPUT) {
                // User entered URL, now ask for Text
                stateData.target_url = text;
                await this.setState(userId, ACTIONS.CREATE_BUTTON, STEPS.TEXT_INPUT, stateData);

                await TelegramBot.sendMessage(chatId,
                    `🔗 Ссылка принята!\n\nТеперь <b>напишите текст кнопки</b>:`,
                    { parse_mode: 'HTML' }
                );
                return true;
            }

            if (state.step === STEPS.TEXT_INPUT) {
                // Creating the button
                const messageId = stateData.message_id;
                const buttonText = text;
                const buttonType = stateData.button_type; // 'url' or 'message'
                const actionData = (buttonType === 'url') ? stateData.target_url : stateData.target_page_key;

                await BotManager.createButton({
                    message_id: messageId,
                    text: buttonText,
                    button_type: buttonType,
                    action_data: actionData
                });

                await this.clearState(userId);
                await TelegramBot.sendMessage(chatId, "✅ <b>Кнопка успешно создана!</b>", { parse_mode: 'HTML' });

                // Show updated message menu
                await this.showEditMessage(chatId, undefined, messageId, true);

                return true;
            }
        }

        return false;
    }

    // Helpers
    static async showButtonManagement(chatId: number, messageId: number) {
        const messages = await BotManager.getAllMessages();
        const buttons: TelegramInlineKeyboardButton[][] = [];

        messages.forEach(msg => {
            const title = (msg.title || "Без заголовка").substring(0, 30);
            const icon = msg.is_main_menu ? "🏠 " : "";
            buttons.push([{
                text: `${icon}${msg.page_key} — ${title}`,
                callback_data: `admin_edit_message_${msg.id}`
            }]);
        });

        buttons.push([{ text: "🔙 Назад", callback_data: "admin_panel" }]);

        await TelegramBot.editMessageText(chatId, messageId, "📝 <b>СПИСОК СООБЩЕНИЙ</b>\n\nВыберите страницу для редактирования:", {
            parse_mode: 'HTML',
            reply_markup: { inline_keyboard: buttons }
        });
    }

    static async showEditMessage(chatId: number, messageId: number | undefined, targetMsgId: string, isNewMessage: boolean = false) {
        const msg = await BotManager.getMessageById(targetMsgId);
        if (!msg) {
            if (messageId) {
                await TelegramBot.editMessageText(chatId, messageId, "❌ Сообщение не найдено");
            }
            return;
        }

        const buttons: TelegramInlineKeyboardButton[][] = [
            [{ text: "➕ Добавить кнопку", callback_data: `admin_create_button_msg_${targetMsgId}` }],
            [{ text: "✏️ Изменить текст", callback_data: `admin_edit_msg_text_${targetMsgId}` }],
            [{ text: "🔙 Назад", callback_data: "admin_button_management" }]
        ];

        // We also list current buttons to delete/edit them
        // (Simplified: just list count for now or simple list)

        const text = `⚙️ <b>Редактирование: ${msg.page_key}</b>\n\nТекст:\n<i>${msg.text}</i>`;

        if (isNewMessage) {
            await TelegramBot.sendMessage(chatId, text, {
                parse_mode: 'HTML',
                reply_markup: { inline_keyboard: buttons }
            });
        } else if (messageId) {
            await TelegramBot.editMessageText(chatId, messageId, text, {
                parse_mode: 'HTML',
                reply_markup: { inline_keyboard: buttons }
            });
        }
    }
}
