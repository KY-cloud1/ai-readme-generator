import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    // Store settings in a cookie for client-side persistence
    // In production, this would be stored in a database
    const settingsCookie = new URLSearchParams();
    settingsCookie.set("settings", JSON.stringify(body));

    return NextResponse.json({ success: true }, {
      headers: {
        "Set-Cookie": `settings=${settingsCookie.toString()}; path=/; HttpOnly; Secure; SameSite=Strict`
      }
    });
  } catch (error) {
    console.error("Failed to store settings:", error);
    return NextResponse.json(
      { error: "Failed to store settings" },
      { status: 500 }
    );
  }
}
