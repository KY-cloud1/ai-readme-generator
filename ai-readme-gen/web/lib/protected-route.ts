import { NextRequest, NextResponse } from 'next/server';
import { getSessionUser } from '@/lib/auth';

/**
 * Middleware to protect API routes
 * Use this decorator/function to protect routes
 */
export async function requireAuth(request: NextRequest): Promise<NextResponse> {
  const session = await getSessionUser();

  if (!session) {
    return NextResponse.json(
      { error: 'Not authenticated' },
      { status: 401 }
    );
  }

  request.headers.set('X-User-Id', session.userId);
  request.headers.set('X-User-Email', session.email);

  return NextResponse.next();
}

/**
 * Check if request has user headers
 */
export function hasAuthHeaders(request: NextRequest): boolean {
  return request.headers.has('X-User-Id') && request.headers.has('X-User-Email');
}
