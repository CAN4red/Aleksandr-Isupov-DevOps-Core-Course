export interface Env {
  APP_NAME: string;
  COURSE_NAME: string;
  API_TOKEN: string;
  ADMIN_EMAIL: string;
  SETTINGS: KVNamespace;
}

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);
    
    // Log request for observability
    console.log(`[${new Date().toISOString()}] path=${url.pathname} colo=${request.cf?.colo} country=${request.cf?.country}`);

    // Route handling
    if (url.pathname === "/health") {
      return Response.json({ 
        status: "ok", 
        timestamp: new Date().toISOString(),
        worker: env.APP_NAME 
      });
    }

    if (url.pathname === "/") {
      return Response.json({
        app: env.APP_NAME,
        course: env.COURSE_NAME,
        message: "Hello from Cloudflare Workers Edge!",
        timestamp: new Date().toISOString(),
        version: "1.0.0"
      });
    }

    if (url.pathname === "/edge") {
      // Return edge metadata from Cloudflare
      return Response.json({
        colo: request.cf?.colo || "unknown",
        country: request.cf?.country || "unknown",
        city: request.cf?.city || "unknown",
        region: request.cf?.region || "unknown",
        asn: request.cf?.asn || "unknown",
        asOrganization: request.cf?.asOrganization || "unknown",
        httpProtocol: request.cf?.httpProtocol || "unknown",
        tlsVersion: request.cf?.tlsVersion || "unknown",
        edgeRequestTimestamp: new Date().toISOString()
      });
    }

    if (url.pathname === "/counter") {
      // KV-backed counter for persistence
      const raw = await env.SETTINGS.get("visits");
      const visits = Number(raw ?? "0") + 1;
      await env.SETTINGS.put("visits", String(visits));
      
      return Response.json({ 
        visits,
        message: "This counter persists across deployments using Workers KV"
      });
    }

    if (url.pathname === "/config") {
      // Show configuration (secrets masked for security)
      return Response.json({
        appName: env.APP_NAME,
        courseName: env.COURSE_NAME,
        apiTokenConfigured: env.API_TOKEN ? "yes (secret)" : "no",
        adminEmailConfigured: env.ADMIN_EMAIL ? "yes (secret)" : "no",
        kvNamespaceBound: env.SETTINGS ? "yes" : "no",
        note: "Secrets are never exposed in responses - only their presence is indicated"
      });
    }

    if (url.pathname === "/secrets-check") {
      // Verify secrets are accessible (but don't expose values)
      const tokenLength = env.API_TOKEN ? env.API_TOKEN.length : 0;
      const emailDomain = env.ADMIN_EMAIL ? env.ADMIN_EMAIL.split('@')[1] : 'none';
      
      return Response.json({
        apiTokenPresent: tokenLength > 0,
        apiTokenLength: tokenLength,
        adminEmailDomain: emailDomain,
        message: "Secrets are properly configured and accessible"
      });
    }

    // 404 for unknown routes
    return new Response("Not Found", { 
      status: 404,
      headers: { "Content-Type": "text/plain" }
    });
  },
};
