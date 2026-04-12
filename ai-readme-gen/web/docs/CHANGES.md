# Authentication and Persistence - Changes Summary

## Overview

This document summarizes the changes made to fix the following issues:
- No persistence layer (replaced with SQLite + Prisma)
- No authentication (added JWT-based auth system)
- Settings not working (fixed with database persistence)
- API key feature incomplete (added full CRUD for API keys)

---

## New Files Created

### Authentication System
- `src/lib/auth.ts` - JWT token generation and verification
- `src/lib/password.ts` - Password hashing and validation
- `src/lib/auth-context.tsx` - React context for client-side auth state
- `src/lib/protected-route.ts` - Helper for protecting routes

### API Routes (Authentication)
- `src/app/api/auth/login/route.ts` - User login endpoint
- `src/app/api/auth/register/route.ts` - User registration endpoint
- `src/app/api/auth/logout/route.ts` - User logout endpoint
- `src/app/api/auth/me/route.ts` - Get current user session

### API Routes (API Keys)
- `src/app/api/api-keys/route.ts` - List API keys
- `src/app/api/api-keys/[id]/route.ts` - Get and delete specific API key

### API Routes (Updated)
- `src/app/api/projects/route.ts` - Now requires authentication
- `src/app/api/projects/[id]/route.ts` - Now requires authentication
- `src/app/api/settings/route.ts` - Now requires authentication
- `src/app/api/settings/store/route.ts` - Now requires authentication
- `src/app/api/settings/retrieve/route.ts` - Now requires authentication

### Pages
- `src/app/login/page.tsx` - Login page
- `src/app/register/page.tsx` - Registration page
- `src/app/layout.tsx` - Updated with AuthProvider

### Database
- `prisma/schema.prisma` - Prisma schema with all models
- `prisma/seed.ts` - Database seed script

### Tests
- `tests/auth.test.ts` - Authentication tests
- `tests/projects.test.ts` - Project management tests
- `tests/settings.test.ts` - Settings tests
- `tests/api-keys.test.ts` - API key tests
- `tests/setup.ts` - Test setup

### Configuration
- `.env.example` - Environment variable template
- `.env.local` - Local development environment
- `.gitignore` - Git ignore rules
- `jest.config.js` - Jest configuration
- `docs/SETUP.md` - Setup documentation

### Utilities
- `src/middleware.ts` - Next.js middleware for auth

---

## Database Schema

### User Model
```prisma
model User {
  id        String   @id @default(uuid())
  email     String   @unique
  name      String?
  password  String
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt

  sessions  Session[]
  apiKeys   ApiKey[]
  settings  Settings?
}
```

### Session Model
```prisma
model Session {
  id        String   @id @default(uuid())
  userId    String
  user      User     @relation(fields: [userId], references: [id], onDelete: Cascade)
  token     String   @unique
  expiresAt DateTime
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
}
```

### ApiKey Model
```prisma
model ApiKey {
  id          String   @id @default(uuid())
  userId      String
  user        User     @relation(fields: [userId], references: [id], onDelete: Cascade)
  name        String
  key         String   @unique
  prefix      String   @db.Collate("BINARY") @db.Binary
  permissions String[]
  isActive    Boolean  @default(true)
  lastUsedAt  DateTime?
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt
}
```

### Settings Model
```prisma
model Settings {
  id        String   @id @default(uuid())
  userId    String   @unique
  user      User     @relation(fields: [userId], references: [id], onDelete: Cascade)
  apiKey    String?
  timeout   Int      @default(300)
  model     String   @default("claude-3-5-sonnet-20240620")
  autoDownload Boolean @default(true)
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
}
```

### Project Model
```prisma
model Project {
  id          String   @id @default(uuid())
  userId      String
  user        User     @relation(fields: [userId], references: [id], onDelete: Cascade)
  name        String
  path        String
  status      String   @default("pending")
  readmePath  String?
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt
}
```

---

## API Changes

### Authentication Endpoints

#### POST /api/auth/register
Register a new user
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123",
  "name": "User Name"
}
```

#### POST /api/auth/login
Login with email and password
```json
{
  "email": "user@example.com",
  "password": "password"
}
```

#### POST /api/auth/logout
Logout current user

#### GET /api/auth/me
Get current user session

### API Key Endpoints

#### POST /api/api-keys
Create a new API key
```json
{
  "name": "My API Key"
}
```

#### GET /api/api-keys
List all active API keys for current user

#### GET /api/api-keys/[id]
Get specific API key details

#### DELETE /api/api-keys/[id]
Deactivate API key

### Protected Endpoints

All the following endpoints now require authentication:
- GET/POST /api/projects
- DELETE /api/projects?id=...
- GET /api/projects/[id]
- PUT /api/projects/[id]
- GET/POST /api/settings
- POST /api/settings/store
- GET /api/settings/retrieve

---

## Security Features

1. **Password Hashing**: All passwords are hashed with bcrypt (12 rounds)
2. **JWT Tokens**: Session tokens use JWT with 7-day expiry
3. **HttpOnly Cookies**: Session tokens are stored in httpOnly cookies
4. **Secure Cookies**: Cookies are secure in production (HTTPS only)
5. **SameSite Cookies**: CSRF protection with SameSite=lax
6. **API Key Management**: API keys can be created, listed, and deactivated
7. **User Isolation**: Users can only access their own data

---

## Migration Notes

The in-memory Map storage has been replaced with a database-driven approach:
- `src/app/api/projects/storage.ts` - Now uses PrismaClient
- `src/app/api/settings/storage.ts` - Now uses PrismaClient

All API routes now require authentication via JWT tokens.

---

## Next Steps

1. Run `npm install` to install all dependencies
2. Run `npm run prisma:generate` to generate Prisma Client
3. Run `npm run prisma:migrate` to create database tables
4. Run `npm run prisma:seed` to seed demo data (optional)
5. Start the dev server with `npm run dev`
6. Register a new account or login with demo credentials
