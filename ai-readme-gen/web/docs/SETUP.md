# Setup Instructions

## Prerequisites

- Node.js 18.x or higher
- npm or yarn
- SQLite (comes with Node.js)

## Initial Setup

1. **Install dependencies**
   ```bash
   npm install
   ```

2. **Generate Prisma Client**
   ```bash
   npm run prisma:generate
   ```

3. **Run database migrations**
   ```bash
   npm run prisma:migrate
   ```

4. **Seed the database (optional)**
   ```bash
   npm run prisma:seed
   ```

5. **Start the development server**
   ```bash
   npm run dev
   ```

## Environment Variables

Copy `.env.example` to `.env.local` and configure:

```bash
DATABASE_URL="file:./dev.db"
JWT_SECRET="your-secret-key-change-in-production"
NEXT_PUBLIC_API_URL="http://localhost:8000"
```

## Testing

Run tests:
```bash
npm test
```

Run tests in watch mode:
```bash
npm run test:watch
```

Run tests with coverage:
```bash
npm run test:coverage
```

## Database Management

View database in Prisma Studio:
```bash
npm run prisma:studio
```

Reset database:
```bash
npx prisma migrate reset
```

## Demo Credentials

After seeding, you can login with:
- Email: `demo@example.com`
- Password: `demo123`

Or register a new account at `/register`.
