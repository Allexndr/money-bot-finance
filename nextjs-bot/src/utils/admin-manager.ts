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
    EDIT_BUTTON_TEXT: 'edit_button_text',
    EDIT_BUTTON_URL: 'edit_button_url',
    CREATE_PAGE_FOR_BUTTON: 'create_page_for_button',
    EDIT_BUTTON_TARGET: 'edit_button_target', // Replaces simple URL edit
};

const STEPS = {
    INITIAL_TYPE_SELECTION: 'initial_type_selection',
    TEXT_INPUT: 'text_input',
    URL_INPUT: 'url_input',
    PAGE_SELECT: 'page_select',
    ENTER_KEY: 'enter_key',
    ENTER_TITLE: 'enter_title',
    ENTER_TEXT: 'enter_text',
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
                    { text: "📄 Выбрать страницу", callback_data: `admin_btn_creation_type_message_${msgId}` }
                ],
                [
                    { text: "🆕 Новая страница", callback_data: `admin_btn_creation_type_newpage_${msgId}` }
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
            const typeKey = parts.pop(); // 'url', 'message', 'newpage'

            const state = await this.getState(userId);

            // Can be CREATE_BUTTON or EDIT_BUTTON_TARGET
            const isEditing = state?.action === ACTIONS.EDIT_BUTTON_TARGET;
            const action = isEditing ? ACTIONS.EDIT_BUTTON_TARGET : ACTIONS.CREATE_BUTTON;

            // If editing, we have button_id in state data, need to preserve it
            const stateData = state ? JSON.parse(state.data) : { message_id: msgId };
            stateData.button_type = (typeKey === 'newpage') ? 'message' : typeKey; // 'newpage' creates a 'message' type button
            stateData.is_creating_new_page = (typeKey === 'newpage');

            if (typeKey === 'url') {
                await this.setState(userId, action, STEPS.URL_INPUT, stateData);
                await TelegramBot.editMessageText(chatId, messageId,
                    "🔗 <b>Отправьте ссылку</b>\n\nПросто пришлите ссылку, которая должна открываться при нажатии.\n<i>Обязательно с https://</i>",
                    {
                        parse_mode: 'HTML',
                        reply_markup: { inline_keyboard: [[{ text: "🔙 Отмена", callback_data: isEditing ? `admin_manage_btn_${stateData.button_id}` : `admin_create_button_msg_${msgId}` }]] }
                    }
                );
            } else if (typeKey === 'message') {
                await this.setState(userId, action, STEPS.PAGE_SELECT, stateData);

                // Show pages
                const messages = await BotManager.getAllMessages();
                const pageButtons: TelegramInlineKeyboardButton[][] = [];
                messages.forEach(msg => {
                    pageButtons.push([{
                        text: `📄 ${msg.title || msg.page_key}`,
                        callback_data: `admin_create_btn_select_page_${msgId}_${msg.page_key}` // Handler will need adjustment for edit
                    }]);
                });
                pageButtons.push([{ text: "🔙 Отмена", callback_data: isEditing ? `admin_manage_btn_${stateData.button_id}` : `admin_create_button_msg_${msgId}` }]);

                await TelegramBot.editMessageText(chatId, messageId,
                    "📄 <b>Выберите страницу из списка:</b>",
                    {
                        parse_mode: 'HTML',
                        reply_markup: { inline_keyboard: pageButtons }
                    }
                );
            } else if (typeKey === 'newpage') {
                // New Page Flow nested in button creation
                await this.setState(userId, ACTIONS.CREATE_PAGE_FOR_BUTTON, STEPS.ENTER_KEY, stateData);
                await TelegramBot.editMessageText(chatId, messageId,
                    "🆕 <b>Создание страницы для кнопки</b>\n\nВведите уникальный <b>ключ страницы</b> (например: <code>details_about_us</code>):",
                    {
                        parse_mode: 'HTML',
                        reply_markup: { inline_keyboard: [[{ text: "🔙 Отмена", callback_data: isEditing ? `admin_manage_btn_${stateData.button_id}` : `admin_create_button_msg_${msgId}` }]] }
                    }
                );
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

                // If editing, we just save immediately
                if (state.action === ACTIONS.EDIT_BUTTON_TARGET) {
                    await BotManager.updateButton(stateData.button_id, {
                        button_type: 'message',
                        action_data: pageKey
                    });
                    await this.clearState(userId);
                    await TelegramBot.sendMessage(chatId, "✅ <b>Цель кнопки обновлена!</b>", { parse_mode: 'HTML' });
                    const btn = await getPrismaClient()?.botButton.findUnique({ where: { id: stateData.button_id } });
                    await this.showEditMessage(chatId, undefined, btn?.message_id || '');
                    return;
                }

                // If creating, ask for text
                await this.setState(userId, ACTIONS.CREATE_BUTTON, STEPS.TEXT_INPUT, stateData);

                await TelegramBot.editMessageText(chatId, messageId,
                    `✅ Выбрана страница: <b>${pageKey}</b>\n\nТеперь <b>напишите текст кнопки</b>:`,
                    {
                        parse_mode: 'HTML',
                        reply_markup: { inline_keyboard: [[{ text: "🔙 Отмена", callback_data: `admin_create_button_msg_${msgId}` }]] }
                    }
                );
            }
            return;
        }

        // Create Page Flow (standalone)
        if (data === 'admin_create_page_start') {
            await this.setState(userId, 'create_page', 'enter_key', {});
            await TelegramBot.editMessageText(chatId, messageId,
                "🆕 <b>Создание новой страницы</b>\n\nВведите уникальный <b>ключ страницы</b> (например: <code>about_us</code>):",
                { parse_mode: 'HTML', reply_markup: { inline_keyboard: [[{ text: "🔙 Отмена", callback_data: "admin_button_management" }]] } }
            );
            return;
        }


        // Auto-create handlers for missing pages
        if (data.startsWith('admin_auto_')) {
            const action = data.substring(11, 14); // txt, btn, set
            const pageKey = data.substring(15);

            // Create the page with defaults
            const newMsg = await BotManager.createMessage({
                page_key: pageKey,
                title: `Страница ${pageKey}`,
                text: `Текст страницы ${pageKey}. Измените его.`,
                is_main_menu: false
            });

            // Redirect to actual handler
            if (action === 'txt') {
                // Simulate admin_edit_msg_text_{id}
                // We can't just recurse easily without refactoring, so we duplicate logic or call a helper?
                // Let's just setState manually as if we clicked the buttons.

                await this.setState(userId, ACTIONS.EDIT_MESSAGE_TEXT, STEPS.TEXT_INPUT, { message_id: newMsg.id });
                await TelegramBot.editMessageText(chatId, messageId, "📝 <b>Введите новый текст сообщения:</b>\n(Поддерживается HTML разметка)", {
                    parse_mode: 'HTML', reply_markup: { inline_keyboard: [[{ text: "🔙 Отмена", callback_data: `admin_edit_message_${newMsg.id}` }]] }
                });
            } else if (action === 'btn') {
                // Simulate admin_create_button_msg_{id}
                await this.setState(userId, ACTIONS.CREATE_BUTTON, STEPS.INITIAL_TYPE_SELECTION, { message_id: newMsg.id });
                const text = "➕ <b>ДОБАВЛЕНИЕ КНОПКИ</b>\n\n<b>Куда должна вести эта кнопка?</b>\n\n";
                // Re-use logic from create button flow...
                const buttons: TelegramInlineKeyboardButton[][] = [
                    [
                        { text: "🔗 Ссылка на сайт", callback_data: `admin_btn_creation_type_url_${newMsg.id}` },
                        { text: "📄 Выбрать страницу", callback_data: `admin_btn_creation_type_message_${newMsg.id}` }
                    ],
                    [
                        { text: "🆕 Новая страница", callback_data: `admin_btn_creation_type_newpage_${newMsg.id}` }
                    ],
                    [
                        { text: "🔙 Отмена", callback_data: `admin_edit_message_${newMsg.id}` }
                    ]
                ];
                await TelegramBot.editMessageText(chatId, messageId, text, {
                    parse_mode: 'HTML', reply_markup: { inline_keyboard: buttons }
                });

            } else if (action === 'set') {
                await this.showEditMessage(chatId, messageId, newMsg.id);
            }
            return;
        }

        // Delete Page Flow
        if (data.startsWith('admin_delete_page_')) {
            const msgId = data.split('_').pop() || '';
            await BotManager.deleteMessage(msgId);
            await TelegramBot.answerCallbackQuery(query.id, { text: "Страница удалена" });
            await this.showButtonManagement(chatId, messageId);
            return;
        }

        // Manage Button Flow
        if (data.startsWith('admin_manage_btn_')) {
            const btnId = data.split('_').pop() || '';

            const btn = await getPrismaClient()?.botButton.findUnique({ where: { id: btnId } });

            if (btn) {
                const buttons: TelegramInlineKeyboardButton[][] = [
                    [
                        { text: "⬆️ Вверх", callback_data: `admin_mv_u_${btnId}` },
                        { text: "⬇️ Вниз", callback_data: `admin_mv_d_${btnId}` }
                    ],
                    [
                        { text: "✏️ Текст кнопки", callback_data: `admin_edit_btn_text_${btnId}` }
                    ]
                ];

                // If button links to a page (message type), add "Edit Content Inside" shortcut
                if (btn.button_type === 'message') {
                    const targetPage = await BotManager.getMessageByKey(btn.action_data);

                    // Go directly to editing the inner page
                    const editContentCallback = targetPage
                        ? `admin_edit_message_${targetPage.id}`
                        : `admin_auto_set_${btn.action_data}`;

                    buttons.push([{
                        text: "📝 Редактировать содержимое",
                        callback_data: editContentCallback
                    }]);
                } else {
                    // If it's a URL button, allow changing the URL
                    buttons.push([{
                        text: "🔗 Изменить ссылку",
                        callback_data: `admin_edit_btn_target_${btnId}`
                    }]);
                }

                buttons.push([{ text: "❌ Удалить кнопку", callback_data: `admin_delete_btn_${btnId}` }]);
                buttons.push([{ text: "🔙 Назад", callback_data: `admin_edit_message_${btn.message_id}` }]);

                const description = btn.button_type === 'url'
                    ? `Ссылка: ${btn.action_data}`
                    : `Ведет к странице: ${btn.action_data}`;

                await TelegramBot.editMessageText(chatId, messageId, `<b>Кнопка:</b> ${btn.text}\n\n${description}`, {
                    parse_mode: 'HTML',
                    reply_markup: { inline_keyboard: buttons }
                });
            } else {
                await TelegramBot.editMessageText(chatId, messageId, "❌ Кнопка не найдена", {
                    reply_markup: { inline_keyboard: [[{ text: "🔙 Назад", callback_data: "admin_panel" }]] }
                });
            }
            return;
        }

        // Edit Button Target Handler
        if (data.startsWith('admin_edit_btn_target_')) {
            const btnId = data.split('_').pop() || '';
            const btn = await getPrismaClient()?.botButton.findUnique({ where: { id: btnId } });
            if (btn) {
                await this.setState(userId, ACTIONS.EDIT_BUTTON_TARGET, STEPS.INITIAL_TYPE_SELECTION, { button_id: btnId, message_id: btn.message_id });

                const buttons: TelegramInlineKeyboardButton[][] = [
                    [
                        { text: "🔗 Ссылка на сайт", callback_data: `admin_btn_creation_type_url_${btn.message_id}` }, // We reuse these but state action is EDIT
                        { text: "📄 Другая страница", callback_data: `admin_btn_creation_type_message_${btn.message_id}` }
                    ],
                    [
                        { text: "🆕 Новая страница", callback_data: `admin_btn_creation_type_newpage_${btn.message_id}` }
                    ],
                    [
                        { text: "🔙 Отмена", callback_data: `admin_manage_btn_${btnId}` }
                    ]
                ];

                await TelegramBot.editMessageText(chatId, messageId, "🎯 <b>Изменение цели кнопки</b>\n\nКуда она должна вести?", {
                    parse_mode: 'HTML',
                    reply_markup: { inline_keyboard: buttons }
                });
            }
            return;
        }

        if (data.startsWith('admin_edit_btn_text_')) {
            const btnId = data.split('_').pop() || '';
            const btn = await getPrismaClient()?.botButton.findUnique({ where: { id: btnId } });
            if (btn) {
                await this.setState(userId, ACTIONS.EDIT_BUTTON_TEXT, STEPS.TEXT_INPUT, { button_id: btnId });
                await TelegramBot.editMessageText(chatId, messageId, `✏️ <b>Введите новый текст для кнопки:</b>\n\nТекущий: ${btn.text}`, {
                    parse_mode: 'HTML',
                    reply_markup: { inline_keyboard: [[{ text: "🔙 Отмена", callback_data: `admin_manage_btn_${btnId}` }]] }
                });
            }
            return;
        }

        if (data.startsWith('admin_delete_btn_')) {
            const btnId = data.split('_').pop() || '';
            const btn = (await getPrismaClient()?.botButton.findUnique({ where: { id: btnId } }));
            if (btn) {
                await BotManager.deleteButton(btnId);
                await TelegramBot.answerCallbackQuery(query.id, { text: "Кнопка удалена" });
                await this.showEditMessage(chatId, messageId, btn.message_id);
            }
            return;
        }

        // Edit Message Text/Title handlers
        if (data.startsWith('admin_edit_msg_text_')) {
            const msgId = data.split('_').pop() || '';
            await this.setState(userId, ACTIONS.EDIT_MESSAGE_TEXT, STEPS.TEXT_INPUT, { message_id: msgId });
            await TelegramBot.editMessageText(chatId, messageId, "📝 <b>Введите новый текст сообщения:</b>\n(Поддерживается HTML разметка)", {
                parse_mode: 'HTML', reply_markup: { inline_keyboard: [[{ text: "🔙 Отмена", callback_data: `admin_edit_message_${msgId}` }]] }
            });
            return;
        }

        if (data.startsWith('admin_edit_msg_title_')) {
            const msgId = data.split('_').pop() || '';
            await this.setState(userId, ACTIONS.EDIT_MESSAGE_TITLE, STEPS.TEXT_INPUT, { message_id: msgId });
            await TelegramBot.editMessageText(chatId, messageId, "🏷 <b>Введите новый заголовок (для админки):</b>", {
                parse_mode: 'HTML', reply_markup: { inline_keyboard: [[{ text: "🔙 Отмена", callback_data: `admin_edit_message_${msgId}` }]] }
            });
            return;
        }

        if (data.startsWith('admin_mv_')) {
            const parts = data.split('_');
            const btnId = parts.pop() || '';
            const direction = data.startsWith('admin_mv_u_') ? 'up' : 'down';

            const btn = await getPrismaClient()?.botButton.findUnique({ where: { id: btnId } });
            if (btn) {
                // Ensure orders are sequential before moving
                await BotManager.normalizeButtonOrders(btn.message_id);

                const allButtons = await BotManager.getButtonsForMessage(btn.message_id);
                const currentIndex = allButtons.findIndex(b => b.id === btn.id);

                if (direction === 'up' && currentIndex > 0) {
                    const prevBtn = allButtons[currentIndex - 1];
                    const currBtn = allButtons[currentIndex];
                    await BotManager.updateButton(currBtn.id, { order: prevBtn.order, row: prevBtn.row });
                    await BotManager.updateButton(prevBtn.id, { order: currBtn.order, row: currBtn.row });
                } else if (direction === 'down' && currentIndex < allButtons.length - 1) {
                    const nextBtn = allButtons[currentIndex + 1];
                    const currBtn = allButtons[currentIndex];
                    await BotManager.updateButton(currBtn.id, { order: nextBtn.order, row: nextBtn.row });
                    await BotManager.updateButton(nextBtn.id, { order: currBtn.order, row: currBtn.row });
                }

                await this.showEditMessage(chatId, messageId, btn.message_id);
            }
            return;
        }

    }

    static async handleUserInput(chatId: number, userId: number, text: string) {
        if (!this.isAdmin(userId)) return false;

        const state = await this.getState(userId);
        if (!state) return false;

        const stateData = JSON.parse(state.data);

        if (state.action === ACTIONS.CREATE_BUTTON || state.action === ACTIONS.EDIT_BUTTON_TARGET) {
            const isEditing = (state.action === ACTIONS.EDIT_BUTTON_TARGET);

            if (state.step === STEPS.URL_INPUT) { // Handling URL input
                // User entered URL
                // Check if editing: save immediately. Creating: ask for text.
                if (!text.startsWith('http')) {
                    await TelegramBot.sendMessage(chatId, "⚠️ Ссылка должна начинаться с https://. Попробуйте снова:");
                    return true;
                }

                if (isEditing) {
                    await BotManager.updateButton(stateData.button_id, {
                        button_type: 'url',
                        action_data: text
                    });
                    await this.clearState(userId);
                    await TelegramBot.sendMessage(chatId, "✅ <b>Ссылка кнопки обновлена!</b>", { parse_mode: 'HTML' });
                    const btn = await getPrismaClient()?.botButton.findUnique({ where: { id: stateData.button_id } });
                    await this.showEditMessage(chatId, undefined, btn?.message_id || '');
                    return true;
                } else {
                    stateData.target_url = text;
                    await this.setState(userId, ACTIONS.CREATE_BUTTON, STEPS.TEXT_INPUT, stateData);
                    await TelegramBot.sendMessage(chatId, `🔗 Ссылка принята!\n\nТеперь <b>напишите текст кнопки</b>:`, { parse_mode: 'HTML' });
                    return true;
                }
            }

            if (state.step === STEPS.TEXT_INPUT && !isEditing) {
                // Creating the button (Last step for creation)
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
                await this.showEditMessage(chatId, undefined, messageId, true);
                return true;
            }
        }

        // Handle CREATE_PAGE_FOR_BUTTON flow
        if (state.action === ACTIONS.CREATE_PAGE_FOR_BUTTON) {
            if (state.step === STEPS.ENTER_KEY) {
                stateData.page_key = text;
                await this.setState(userId, ACTIONS.CREATE_PAGE_FOR_BUTTON, STEPS.ENTER_TITLE, stateData);
                await TelegramBot.sendMessage(chatId, "Введите <b>заголовок страницы</b> (для админки):", { parse_mode: 'HTML' });
                return true;
            }
            if (state.step === STEPS.ENTER_TITLE) {
                stateData.title = text;
                await this.setState(userId, ACTIONS.CREATE_PAGE_FOR_BUTTON, STEPS.ENTER_TEXT, stateData);
                await TelegramBot.sendMessage(chatId, "Введите <b>текст сообщения</b> (содержимое страницы):", { parse_mode: 'HTML' });
                return true;
            }
            if (state.step === STEPS.ENTER_TEXT) {
                const newMsg = await BotManager.createMessage({
                    page_key: stateData.page_key,
                    title: stateData.title,
                    text: text,
                    is_main_menu: false
                });

                // If we were editing a button target to this new page:
                if (stateData.button_id) { // This means we came from EDIT_BUTTON_TARGET
                    await BotManager.updateButton(stateData.button_id, {
                        button_type: 'message',
                        action_data: newMsg.page_key
                    });
                    await this.clearState(userId);
                    await TelegramBot.sendMessage(chatId, `✅ <b>Страница создана и кнопка обновлена!</b>\n\nКлюч: ${newMsg.page_key}`, { parse_mode: 'HTML' });
                    const btn = await getPrismaClient()?.botButton.findUnique({ where: { id: stateData.button_id } });
                    await this.showEditMessage(chatId, undefined, btn?.message_id || '');
                    return true;
                } else {
                    // Creating new button to this page
                    stateData.target_page_key = newMsg.page_key;
                    // Hand back to CREATE_BUTTON flow for text input
                    await this.setState(userId, ACTIONS.CREATE_BUTTON, STEPS.TEXT_INPUT, stateData);
                    await TelegramBot.sendMessage(chatId, `✅ <b>Страница создана!</b> (${newMsg.page_key})\n\nТеперь <b>напишите текст кнопки</b>:`, { parse_mode: 'HTML' });
                    return true;
                }
            }
        }

        if (state.action === 'create_page') {
            if (state.step === 'enter_key') {
                stateData.page_key = text;
                await this.setState(userId, 'create_page', 'enter_title', stateData);
                await TelegramBot.sendMessage(chatId, "Введите <b>заголовок страницы</b> (для списка в админке):", { parse_mode: 'HTML' });
                return true;
            }
            if (state.step === 'enter_title') {
                stateData.title = text;
                await this.setState(userId, 'create_page', 'enter_text', stateData);
                await TelegramBot.sendMessage(chatId, "Введите <b>текст сообщения</b> (содержимое страницы):", { parse_mode: 'HTML' });
                return true;
            }
            if (state.step === 'enter_text') {
                const newMsg = await BotManager.createMessage({
                    page_key: stateData.page_key,
                    title: stateData.title,
                    text: text,
                    is_main_menu: false
                });
                await this.clearState(userId);
                await TelegramBot.sendMessage(chatId, "✅ <b>Страница создана!</b>", { parse_mode: 'HTML' });
                await this.showEditMessage(chatId, undefined, newMsg.id, true);
                return true;
            }
        }

        if (state.action === ACTIONS.EDIT_MESSAGE_TEXT) {
            await BotManager.updateMessage(stateData.message_id, { text: text });
            await this.clearState(userId);
            await TelegramBot.sendMessage(chatId, "✅ <b>Текст обновлен!</b>", { parse_mode: 'HTML' });
            await this.showEditMessage(chatId, undefined, stateData.message_id, true);
            return true;
        }

        if (state.action === ACTIONS.EDIT_MESSAGE_TITLE) {
            await BotManager.updateMessage(stateData.message_id, { title: text });
            await this.clearState(userId);
            await TelegramBot.sendMessage(chatId, "✅ <b>Заголовок обновлен!</b>", { parse_mode: 'HTML' });
            await this.showEditMessage(chatId, undefined, stateData.message_id, true);
            return true;
        }

        if (state.action === ACTIONS.EDIT_BUTTON_TEXT) {
            const btn = await BotManager.updateButton(stateData.button_id, { text: text });
            await this.clearState(userId);
            await TelegramBot.sendMessage(chatId, "✅ <b>Текст кнопки обновлен!</b>", { parse_mode: 'HTML' });
            // Ideally go back to manage button view, but we need msgId. Let's go to msg edit view
            if (btn) {
                const fullBtn = await getPrismaClient()?.botButton.findUnique({ where: { id: btn.id } });
                await this.showEditMessage(chatId, undefined, fullBtn?.message_id || '', true);
            }
            return true;
        }

        return false;
    }

    // Helpers
    static async showButtonManagement(chatId: number, messageId: number) {
        // User requested: "оставь тут только главное меню пожалуйста и создание новой страницы"
        const buttons: TelegramInlineKeyboardButton[][] = [];

        // Show ONLY Main Menu
        const mainMenu = await BotManager.getMessageByKey('main_menu');
        if (mainMenu) {
            buttons.push([{
                text: "Главное меню", // No icon as requested
                callback_data: `admin_edit_message_${mainMenu.id}`
            }]);
        }

        // Add "Create New Page" button
        buttons.push([{ text: "➕ Создать новую страницу", callback_data: "admin_create_page_start" }]);
        buttons.push([{ text: "🔙 Назад", callback_data: "admin_panel" }]);

        await TelegramBot.editMessageText(chatId, messageId, "📝 <b>УПРАВЛЕНИЕ БОТОМ</b>\n\nВыберите действие:", {
            parse_mode: 'HTML',
            reply_markup: { inline_keyboard: buttons }
        });
    }

    static async showEditMessage(chatId: number, messageId: number | undefined, targetMsgId: string, isNewMessage: boolean = false) {
        // Automatically normalize orders to prevent "Up/Down" glitches
        await BotManager.normalizeButtonOrders(targetMsgId);

        const msg = await BotManager.getMessageById(targetMsgId);
        if (!msg) {
            if (messageId) {
                await TelegramBot.editMessageText(chatId, messageId, "❌ Сообщение не найдено");
            }
            return;
        }

        const msgButtons = await BotManager.getButtonsForMessage(targetMsgId);

        const buttons: TelegramInlineKeyboardButton[][] = [
            [{ text: "➕ Добавить кнопку", callback_data: `admin_create_button_msg_${targetMsgId}` }],
            [{ text: "✏️ Изм. текст", callback_data: `admin_edit_msg_text_${targetMsgId}` }, { text: "🏷 Изм. заголовок", callback_data: `admin_edit_msg_title_${targetMsgId}` }],
        ];

        // List existing buttons for management
        msgButtons.forEach(btn => {
            // User requested: "убери у них значок кнопки этот перед каждый названием"
            const typeHint = btn.button_type === 'url' ? ' [ссылка]' : '';
            buttons.push([{
                text: `${btn.text}${typeHint}`,
                callback_data: `admin_manage_btn_${btn.id}`
            }]);
        });

        if (!msg.is_main_menu) {
            buttons.push([{ text: "❌ Удалить страницу", callback_data: `admin_delete_page_${targetMsgId}` }]);
        }

        buttons.push([{ text: "🔙 Назад к списку", callback_data: "admin_button_management" }]);

        const text = `⚙️ <b>Редактирование: ${msg.page_key}</b>\n\n<b>Заголовок:</b> ${msg.title}\n\n<b>Текст:</b>\n${msg.text}`;

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
