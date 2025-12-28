import { NextResponse } from 'next/server';
import { getPrismaClient } from '../../../lib/prisma';
import { BotManager } from '../../../utils/bot-manager';

export const dynamic = 'force-dynamic';

export async function GET() {
    const diagnosis: any = {
        env: {
            has_mongo_uri: !!process.env.dengi_MONGODB_URI,
            node_env: process.env.NODE_ENV,
        },
        prisma_client: 'unknown',
        db_connection: 'unknown',
        messages_count: 0,
        main_menu_exists: false,
        errors: [],
    };

    try {
        const prisma = getPrismaClient();
        diagnosis.prisma_client = prisma ? 'initialized' : 'null';

        if (prisma) {
            try {
                await prisma.$connect();
                diagnosis.db_connection = 'success';

                const count = await prisma.botMessage.count();
                diagnosis.messages_count = count;

                const mainMenu = await BotManager.getMessageByKey('main_menu');
                diagnosis.main_menu_exists = !!mainMenu;
                diagnosis.main_menu = mainMenu; // Show what we found
            } catch (dbError: any) {
                diagnosis.db_connection = 'failed';
                diagnosis.errors.push(dbError.message);
            }
        } else {
            diagnosis.errors.push('Prisma client returned null');
        }
    } catch (e: any) {
        diagnosis.errors.push(e.message);
    }

    return NextResponse.json(diagnosis);
}
