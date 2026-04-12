import { NextRequest, NextResponse } from "next/server";
import type { Project } from "@/lib/api";

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    // TODO: Get project from database
    // For now, return mock project
    const project: Project = {
      id: params.id,
      name: "Sample Python Project",
      path: "/path/to/sample",
      createdAt: new Date(Date.now() - 86400000).toISOString(),
      updatedAt: new Date(Date.now() - 3600000).toISOString(),
      status: "completed",
    };

    return NextResponse.json(project);
  } catch (error) {
    return NextResponse.json(
      { error: "Failed to get project" },
      { status: 500 }
    );
  }
}
