import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  try {
    const contentType = request.headers.get("content-type");
    if (!contentType || !contentType.includes("application/json")) {
      return NextResponse.json(
        { error: "Content-Type must be application/json" },
        { status: 400 }
      );
    }

    const body = await request.json();

    // Store settings in localStorage (client-side for now)
    // In production, this would be stored in a database
    await fetch("/api/settings/store", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Failed to save settings:", error);
    return NextResponse.json(
      { error: "Failed to save settings" },
      { status: 500 }
    );
  }
}

export async function GET() {
  try {
    // Retrieve settings from localStorage
    const response = await fetch("/api/settings/retrieve");
    return response;
  } catch (error) {
    console.error("Failed to retrieve settings:", error);
    return NextResponse.json(
      { error: "Failed to retrieve settings" },
      { status: 500 }
    );
  }
}
