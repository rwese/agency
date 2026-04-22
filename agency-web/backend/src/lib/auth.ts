import * as bcrypt from 'bcrypt'
import * as jose from 'jose'
import { UserRole } from '@prisma/client'

const JWT_SECRET = new TextEncoder().encode(
  process.env.JWT_SECRET || 'dev-secret-change-in-production'
)
const JWT_EXPIRY = '7d'

export interface JWTPayload {
  userId: string
  username: string
  role: UserRole
  email?: string
}

export interface AuthContext {
  user: JWTPayload | null
  isAuthenticated: boolean
  isAdmin: boolean
}

export async function createToken(payload: JWTPayload): Promise<string> {
  const token = await new jose.SignJWT({
    userId: payload.userId,
    username: payload.username,
    role: payload.role,
    email: payload.email,
  })
    .setProtectedHeader({ alg: 'HS256' })
    .setIssuedAt()
    .setExpirationTime(JWT_EXPIRY)
    .sign(JWT_SECRET)

  return token
}

export async function verifyToken(token: string): Promise<JWTPayload | null> {
  try {
    const { payload } = await jose.jwtVerify(token, JWT_SECRET)

    if (!payload.userId || !payload.username || !payload.role) {
      return null
    }

    return {
      userId: payload.userId as string,
      username: payload.username as string,
      role: payload.role as UserRole,
      email: payload.email as string | undefined,
    }
  } catch {
    return null
  }
}

export async function hashPassword(password: string): Promise<string> {
  return bcrypt.hash(password, 10)
}

export async function verifyPassword(password: string, hash: string): Promise<boolean> {
  return bcrypt.compare(password, hash)
}

export function generateApiKey(): { key: string; hash: string } {
  const key = `agw_sk_${Array.from({ length: 32 }, () =>
    Math.random().toString(36).charAt(2)
  ).join('')}`
  // Simple hash for API key storage (use bcrypt in production)
  const hash = bcrypt.hashSync(key, 10)
  return { key, hash }
}

export function extractTokenFromHeader(authHeader: string | undefined): string | null {
  if (!authHeader) return null
  if (authHeader.startsWith('Bearer ')) {
    return authHeader.slice(7)
  }
  return null
}

export async function getAuthContext(token: string | null): Promise<AuthContext> {
  if (!token) {
    return { user: null, isAuthenticated: false, isAdmin: false }
  }

  const payload = await verifyToken(token)
  if (!payload) {
    return { user: null, isAuthenticated: false, isAdmin: false }
  }

  return {
    user: payload,
    isAuthenticated: true,
    isAdmin: payload.role === UserRole.admin,
  }
}
