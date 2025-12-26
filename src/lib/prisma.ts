const { PrismaClient } = require('@prisma/client');

const globalForPrisma = globalThis as unknown as {
  prisma: typeof PrismaClient | undefined;
};

let prisma: typeof PrismaClient;

export function getPrismaClient() {
  if (!prisma) {
    prisma = new PrismaClient();
    if (process.env.NODE_ENV !== 'production') {
      globalForPrisma.prisma = prisma;
    }
  }
  return prisma;
}

// Для обратной совместимости
export const prismaInstance = getPrismaClient();
