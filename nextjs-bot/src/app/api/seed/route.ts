import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

async function performSeed() {
  const { seedDatabase } = await import('../../../utils/seed-database');
  await seedDatabase();
}

export async function GET() {
  try {
    await performSeed();
    return NextResponse.json({ success: true, message: 'Database seeded successfully' });
  } catch (error: any) {
    console.error('Seed error:', error);
    return NextResponse.json({ error: error.message || 'Failed to seed database' }, { status: 500 });
  }
}

export async function POST() {
  try {
    await performSeed();
    return NextResponse.json({ success: true, message: 'Database seeded successfully' });
  } catch (error: any) {
    console.error('Seed error:', error);
    return NextResponse.json({ error: error.message || 'Failed to seed database' }, { status: 500 });
  }
}
