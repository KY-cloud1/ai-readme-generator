import { PrismaClient } from "@prisma/client";
import bcrypt from "bcryptjs";

const prisma = new PrismaClient();

async function main() {
  // Create a demo user
  const hashedPassword = await bcrypt.hash("demo123", 12);

  const user = await prisma.user.upsert({
    where: { email: "demo@example.com" },
    update: {},
    create: {
      email: "demo@example.com",
      name: "Demo User",
      password: hashedPassword,
    },
  });

  console.log("Demo user created:", user.email);

  // Create demo settings
  await prisma.settings.upsert({
    where: { userId: user.id },
    update: {},
    create: {
      userId: user.id,
      apiKey: "",
      timeout: 300,
      model: "claude-3-5-sonnet-20240620",
      autoDownload: true,
    },
  });

  console.log("Demo settings created");

  // Create demo project
  const demoProject = await prisma.project.create({
    data: {
      userId: user.id,
      name: "Demo Project",
      path: "/demo/path",
      status: "completed",
    },
  });

  console.log("Demo project created:", demoProject.id);
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });