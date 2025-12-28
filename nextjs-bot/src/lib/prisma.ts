let prisma: any = null;

export function getPrismaClient() {
  // Проверяем доступность переменных окружения
  if (!process.env.dengi_MONGODB_URI && process.env.NODE_ENV === 'production') {
    throw new Error('dengi_MONGODB_URI not configured');
  }

  if (!prisma) {
    try {
      const { PrismaClient } = require('@prisma/client');

      // Auto-fix for missing database name in MongoDB URI
      let url = process.env.dengi_MONGODB_URI || '';
      if (url && url.includes('mongodb.net')) {
        const hasDbName = url.match(/mongodb\.net\/([^?]+)/);
        if (!hasDbName) {
          if (url.includes('?')) {
            url = url.replace('mongodb.net/', 'mongodb.net/money_bot');
          } else {
            url = url.endsWith('/') ? url + 'money_bot' : url + '/money_bot';
          }
          console.log('Patched MongoDB URI to include database name: money_bot');
        }
      }

      prisma = new PrismaClient({
        datasources: {
          db: {
            url: url,
          },
        },
      });

      // Глобальное хранение только в development
      if (process.env.NODE_ENV !== 'production') {
        (globalThis as any).prisma = prisma;
      }
    } catch (error) {
      // В случае ошибки во время сборки возвращаем null
      console.error('Failed to initialize Prisma client:', error);
      return null;
    }
  }
  return prisma;
}
