import { NextRequest, NextResponse } from 'next/server';

export async function POST() {
  try {
    const response = NextResponse.json(
      { success: true, message: 'Logged out successfully' },
      {
        headers: {
          'Set-Cookie': await clearSession(),
        },
      }
    );

    response.cookies.delete('session_token');

    return response;
  } catch (error) {
    console.error('Logout error:', error);
    return NextResponse.json(
      { error: 'Failed to logout' },
      { status: 500 }
    );
  }
}

async function clearSession(): Promise<string> {
  const cookieStore = await cookies();
  return cookieStore.delete('session_token').toString();
}
