import { NextRequest, NextResponse } from "next/server";

/**
 * Basic Auth middleware - protects entire site when BASIC_AUTH_USER and
 * BASIC_AUTH_PASSWORD are set (production). When not set, site is open (dev).
 */
export function middleware(request: NextRequest) {
  const user = process.env.BASIC_AUTH_USER;
  const password = process.env.BASIC_AUTH_PASSWORD;

  // Skip auth if credentials not configured (dev mode)
  if (!user || !password) {
    return NextResponse.next();
  }

  const authHeader = request.headers.get("authorization");
  if (!authHeader?.startsWith("Basic ")) {
    return new NextResponse("Authentication required", {
      status: 401,
      headers: {
        "WWW-Authenticate": 'Basic realm="RAG Assistant"',
      },
    });
  }

  const encoded = authHeader.slice(6);
  let decoded: string;
  try {
    decoded = Buffer.from(encoded, "base64").toString("utf-8");
  } catch {
    return new NextResponse("Invalid credentials", { status: 401 });
  }

  const [u, p] = decoded.split(":", 2);
  if (u !== user || p !== password) {
    return new NextResponse("Invalid credentials", { status: 401 });
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all paths except static files and _next
     */
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};
