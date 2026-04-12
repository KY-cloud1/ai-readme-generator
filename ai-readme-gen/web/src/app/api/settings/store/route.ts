import { NextRequest, NextResponse } from 'next/server';
import { getSessionUser } from '@/lib/auth';
import { updateSetting } from './storage';

export async function POST(request: NextRequest) {
  try {
    const session = await getSessionUser();

    if (!session) {
      return NextResponse.json(
        { error: 'Not authenticated' },
        { status: 401 }
      );
    }

    const contentType = request.headers.get('content-type');
    if (!contentType || !contentType.includes('application/json')) {
      return NextResponse.json(
        { error: 'Content-Type must be application/json' },
        { status: 400 }
      );
    }

    const body = await request.json();

    // Update individual settings
    if (body.apiKey !== undefined) {
      await updateSetting(session.userId, 'apiKey', body.apiKey);
    }
    if (body.timeout !== undefined) {
      await updateSetting(session.userId, 'timeout', body.timeout);
    }
    if (body.model !== undefined) {
      await updateSetting(session.userId, 'model', body.model);
    }
    if (body.autoDownload !== undefined) {
      await updateSetting(session.userId, 'autoDownload', body.autoDownload);
    }

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('Failed to store settings:', error);
    return NextResponse.json(
      { error: 'Failed to store settings' },
      { status: 500 }
    );
  }
}
