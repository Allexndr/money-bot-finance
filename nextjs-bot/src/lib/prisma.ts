let prisma: any = null;

export function getPrismaClient() {
  // Проверяем доступность переменных окружения
  if (!process.env.dengi_MONGODB_URI && process.env.NODE_ENV === 'production') {
    throw new Error('dengi_MONGODB_URI not configured');
  }

  if (!prisma) {
    try {
      const { PrismaClient } = require('@prisma/client');
      prisma = new PrismaClient();

      // Глобальное хранение только в development
      if (process.env.NODE_ENV !== 'production') {
        (globalThis as any).prisma = prisma;
      }
    } catch (error) {
      // В случае ошибки во время сборки возвращаем null
      console.warn('Prisma client not available during build');
      return null;
    }
  }
  return prisma;
}
