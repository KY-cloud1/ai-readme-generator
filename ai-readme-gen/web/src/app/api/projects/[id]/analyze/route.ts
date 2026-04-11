import { NextRequest, NextResponse } from "next/server";

// TODO: Configure backend API URL
const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

if (!BACKEND_URL) {
  console.warn("Warning: BACKEND_URL environment variable is not set. Using default fallback.");
}

export async function POST(request: NextRequest) {
  try {
    // Parse JSON body
    let body;
    try {
      body = await request.json();
    } catch (parseError) {
      return NextResponse.json(
        { error: "Invalid JSON body" },
        { status: 400 }
      );
    }

    const { path } = body;

    if (!path) {
      return NextResponse.json(
        { error: "Path is required" },
        { status: 400 }
      );
    }

    // Call backend CLI for analysis
    const response = await fetch(`${BACKEND_URL}/analyze`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ path }),
    });

    if (!response.ok) {
      return NextResponse.json(
        { error: "Backend analysis failed" },
        { status: 500 }
      );
    }

    const result = await response.json();

    return NextResponse.json(result);
  } catch (error) {
    console.error("Failed to analyze project:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
