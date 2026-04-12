import { NextRequest, NextResponse } from "next/server";

export async function GET() {
  try {
    // Retrieve settings from cookie
    const cookies = NextRequest.cookies();
    const settingsCookie = cookies.get("settings");

    if (settingsCookie && settingsCookie.value) {
      return NextResponse.json(JSON.parse(settingsCookie.value));
    }

    return NextResponse.json({});
  } catch (error) {
    console.error("Failed to retrieve settings:", error);
    return NextResponse.json(
      { error: "Failed to retrieve settings" },
      { status: 500 }
    );
  }
}
