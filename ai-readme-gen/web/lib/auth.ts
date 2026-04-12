import { cookies } from 'next/headers';
import { encode, decode } from 'next-jwt';

const JWT_SECRET = process.env.JWT_SECRET || 'your-secret-key-change-in-production';
const JWT_EXPIRY_HOURS = 24 * 7; // 7 days

export interface JWTPayload {
  userId: string;
  email: string;
  roles?: string[];
}

/**
 * Generate a JWT token for a user
 */
export async function generateToken(payload: JWTPayload): Promise<string> {
  const expiresAt = new Date(Date.now() + JWT_EXPIRY_HOURS * 60 * 60 * 1000);
  return encode({
    ...payload,
    exp: Math.floor(expiresAt.getTime() / 1000),
    iat: Math.floor(Date.now() / 1000),
  }, JWT_SECRET);
}

/**
 * Verify and decode a JWT token
 */
export async function verifyToken(token: string): Promise<JWTPayload | null> {
  try {
    const decoded = decode(token, JWT_SECRET);
    const payload = decoded as JWTPayload & { exp?: number };

    if (payload.exp && payload.exp < Math.floor(Date.now() / 1000)) {
      return null; // Token expired
    }

    return payload;
  } catch {
    return null;
  }
}

/**
 * Get user from session cookie
 */
export async function getSessionUser(): Promise<JWTPayload | null> {
  const cookieStore = await cookies();
  const token = cookieStore.get('session_token')?.value;

  if (!token) {
    return null;
  }

  return verifyToken(token);
}

/**
 * Check if a user has a specific permission
 */
export function hasPermission(user: JWTPayload, permission: string): boolean {
  // For now, all authenticated users have full access
  // In the future, you can add role-based permissions
  return true;
}

/**
 * Generate API key for a user
 */
export function generateApiKey(prefix = 'ak_'): string {
  const randomBytes = Math.random().toString(36).substring(2) +
                      Math.random().toString(36).substring(2);
  return `${prefix}${randomBytes.substring(0, 32)}`;
}
