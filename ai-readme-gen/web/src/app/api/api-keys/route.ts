import { NextRequest, NextResponse } from 'next/server';
import { PrismaClient } from '@prisma/client';
import { getSessionUser } from '@/lib/auth';
import { generateApiKey } from '@/lib/auth';

const prisma = new PrismaClient();

export async function POST(request: NextRequest) {
  try {
    const session = await getSessionUser();

    if (!session) {
      return NextResponse.json(
        { error: 'Not authenticated' },
        { status: 401 }
      );
    }

    // Validate content-type header
    const contentType = request.headers.get('content-type');
    if (!contentType || !contentType.includes('application/json')) {
      return NextResponse.json(
        { error: 'Content-Type must be application/json' },
        { status: 400 }
      );
    }

    const body = await request.json();
    const { name } = body;

    if (!name) {
      return NextResponse.json(
        { error: 'Name is required' },
        { status: 400 }
      );
    }

    // Generate new API key
    const apiKey = generateApiKey('ak_');

    // Create API key record
    const apikey = await prisma.apikey.create({
      data: {
        userId: session.userId,
        name,
        key: apiKey,
        prefix: 'ak_',
        permissions: ['projects:read', 'projects:write', 'settings:read', 'settings:write'],
        isActive: true,
      },
    });

    return NextResponse.json({
      ...apikey,
      // Don't expose full key in response for security
      key: '********',
    });
  } catch (error) {
    console.error('Failed to create API key:', error);
    return NextResponse.json(
      { error: 'Failed to create API key' },
      { status: 500 }
    );
  }
}

export async function GET() {
  try {
    const session = await getSessionUser();

    if (!session) {
      return NextResponse.json(
        { error: 'Not authenticated' },
        { status: 401 }
      );
    }

    const apikeys = await prisma.apikey.findMany({
      where: {
        userId: session.userId,
        isActive: true,
      },
      orderBy: { createdAt: 'desc' },
    });

    return NextResponse.json(
      apikeys.map((ak) => ({
        ...ak,
        key: '********',
      }))
    );
  } catch (error) {
    console.error('Failed to get API keys:', error);
    return NextResponse.json(
      { error: 'Failed to get API keys' },
      { status: 500 }
    );
  }
}
