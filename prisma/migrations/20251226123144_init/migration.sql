-- CreateTable
CREATE TABLE "users" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "telegram_id" INTEGER NOT NULL,
    "username" TEXT,
    "first_name" TEXT,
    "last_name" TEXT,
    "created_at" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "is_subscribed" BOOLEAN NOT NULL DEFAULT true
);

-- CreateTable
CREATE TABLE "course_applications" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "user_id" INTEGER NOT NULL,
    "user_telegram_id" INTEGER NOT NULL,
    "username" TEXT,
    "first_name" TEXT,
    "status" TEXT NOT NULL DEFAULT 'pending',
    "created_at" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "processed_at" DATETIME,
    "processed_by" TEXT
);

-- CreateTable
CREATE TABLE "newsletters" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "title" TEXT NOT NULL,
    "content" TEXT NOT NULL,
    "created_at" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "sent_at" DATETIME,
    "is_sent" BOOLEAN NOT NULL DEFAULT false
);

-- CreateTable
CREATE TABLE "bot_messages" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "page_key" TEXT NOT NULL,
    "title" TEXT,
    "text" TEXT NOT NULL,
    "parse_mode" TEXT NOT NULL DEFAULT 'HTML',
    "is_main_menu" BOOLEAN NOT NULL DEFAULT false,
    "created_at" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" DATETIME NOT NULL
);

-- CreateTable
CREATE TABLE "bot_buttons" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "message_id" INTEGER NOT NULL,
    "text" TEXT NOT NULL,
    "button_type" TEXT NOT NULL,
    "action_data" TEXT NOT NULL,
    "row" INTEGER NOT NULL DEFAULT 0,
    "order" INTEGER NOT NULL DEFAULT 0,
    "is_active" BOOLEAN NOT NULL DEFAULT true,
    "created_at" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" DATETIME NOT NULL,
    CONSTRAINT "bot_buttons_message_id_fkey" FOREIGN KEY ("message_id") REFERENCES "bot_messages" ("id") ON DELETE RESTRICT ON UPDATE CASCADE
);

-- CreateIndex
CREATE UNIQUE INDEX "users_telegram_id_key" ON "users"("telegram_id");

-- CreateIndex
CREATE UNIQUE INDEX "bot_messages_page_key_key" ON "bot_messages"("page_key");
