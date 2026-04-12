import { NextRequest, NextResponse } from "next/server";
import type { Project } from "@/lib/api";

export async function POST(request: NextRequest) {
  try {
    // Validate content-type header
    const contentType = request.headers.get("content-type");
    if (!contentType || !contentType.includes("application/json")) {
      return NextResponse.json(
        { error: "Content-Type must be application/json" },
        { status: 400 }
      );
    }

    const body = await request.json();
    const { name, path } = body;

    if (!name || !path) {
      return NextResponse.json(
        { error: "Name and path are required" },
        { status: 400 }
      );
    }

    // TODO: Create project and store in database
    // For now, return a mock project
    const project: Project = {
      id: (Math.random() * 10000).toString(),
      name,
      path,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      status: "pending",
    };

    return NextResponse.json(project);
  } catch (error) {
    if (error instanceof Error && error.message.includes("JSON")) {
      return NextResponse.json(
        { error: "Invalid JSON body" },
        { status: 400 }
      );
    }
    return NextResponse.json(
      { error: "Failed to create project" },
      { status: 500 }
    );
  }
}

export async function GET() {
  // TODO: List projects from database
  // For now, return mock projects
  const projects: Project[] = [
    {
      id: "1",
      name: "Sample Python Project",
      path: "/path/to/sample",
      createdAt: new Date(Date.now() - 86400000).toISOString(),
      updatedAt: new Date(Date.now() - 3600000).toISOString(),
      status: "completed",
    },
  ];

  return NextResponse.json(projects);
}
