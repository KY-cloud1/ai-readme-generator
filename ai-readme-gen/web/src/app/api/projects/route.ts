import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  try {
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
    const project = {
      id: "1",
      name,
      path,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      status: "pending",
    };

    return NextResponse.json(project);
  } catch (error) {
    return NextResponse.json(
      { error: "Failed to create project" },
      { status: 500 }
    );
  }
}

export async function GET() {
  // TODO: List projects from database
  return NextResponse.json([]);
}
