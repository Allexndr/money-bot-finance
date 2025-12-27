-- CreateTable
CREATE TABLE "bot_states" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "telegram_id" INTEGER NOT NULL,
    "action" TEXT NOT NULL,
    "step" TEXT NOT NULL,
    "data" TEXT NOT NULL,
    "updated_at" DATETIME NOT NULL
);

-- CreateIndex
CREATE UNIQUE INDEX "bot_states_telegram_id_key" ON "bot_states"("telegram_id");
