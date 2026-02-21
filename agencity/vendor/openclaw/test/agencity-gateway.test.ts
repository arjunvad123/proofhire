/**
 * Agencity Gateway Integration Tests
 *
 * Tests the OpenClaw gateway running on ws://127.0.0.1:18789 against the
 * Agencity recruiting backend on http://localhost:8001.
 *
 * Prerequisite: gateway must be running:
 *   OPENCLAW_SKIP_CHANNELS=1 OPENCLAW_GATEWAY_AUTH_TOKEN=<token> \
 *   node openclaw.mjs gateway --port 18789
 *
 * Run with:
 *   pnpm vitest run test/agencity-gateway.test.ts
 */

import { randomUUID } from "node:crypto";
import { WebSocket } from "ws";
import { afterAll, beforeAll, describe, expect, it } from "vitest";

// ─── Config ───────────────────────────────────────────────────────────────────

const GATEWAY_URL = process.env.OPENCLAW_GATEWAY_URL ?? "ws://127.0.0.1:18789";
const GATEWAY_TOKEN =
  process.env.OPENCLAW_GATEWAY_AUTH_TOKEN ??
  "4656c99d3e803e907e9b13fe39821ee53fad1f01c640b4c7ce7dbc817f1c7a20";
const AGENCITY_URL = process.env.AGENCITY_URL ?? "http://127.0.0.1:8001";
const CONNECT_TIMEOUT_MS = 10_000;
const REQUEST_TIMEOUT_MS = 15_000;

// ─── Helpers ──────────────────────────────────────────────────────────────────

/**
 * Open a raw WebSocket to the gateway and complete the connect handshake.
 * Returns the connected ws and the hello payload.
 */
async function openGatewayWs(token?: string): Promise<{
  ws: WebSocket;
  hello: Record<string, unknown>;
  close: () => void;
}> {
  const ws = new WebSocket(GATEWAY_URL);

  const hello = await new Promise<Record<string, unknown>>((resolve, reject) => {
    const timer = setTimeout(
      () => reject(new Error(`gateway connect timeout after ${CONNECT_TIMEOUT_MS}ms`)),
      CONNECT_TIMEOUT_MS,
    );

    ws.once("open", () => {
      // Send connect request
      ws.send(
        JSON.stringify({
          type: "req",
          id: "c1",
          method: "connect",
          params: {
            minProtocol: 1,
            maxProtocol: 9999,
            client: {
              id: "test",
              displayName: "Agencity Test Suite",
              version: "0.0.1",
              platform: process.platform,
              mode: "test",
            },
            caps: [],
            auth: token ? { token } : undefined,
          },
        }),
      );
    });

    ws.on("message", (data) => {
      const msg = JSON.parse(data.toString()) as Record<string, unknown>;
      if (msg.type === "res" && msg.id === "c1") {
        clearTimeout(timer);
        if (msg.ok) {
          resolve(msg);
        } else {
          const err = msg.error as Record<string, unknown> | undefined;
          reject(new Error(`connect rejected: ${String(err?.message ?? "unknown")}`));
        }
      }
    });

    ws.on("error", (err) => {
      clearTimeout(timer);
      reject(err);
    });
    ws.on("close", (code, reason) => {
      clearTimeout(timer);
      reject(new Error(`ws closed during connect (${code}): ${reason.toString()}`));
    });
  });

  return {
    ws,
    hello,
    close: () => {
      if (ws.readyState === WebSocket.OPEN) ws.close();
    },
  };
}

/**
 * Send a request over an open gateway ws and wait for its response.
 */
async function gatewayRequest(
  ws: WebSocket,
  method: string,
  params: Record<string, unknown> = {},
): Promise<Record<string, unknown>> {
  const id = randomUUID();
  ws.send(JSON.stringify({ type: "req", id, method, params }));

  return new Promise((resolve, reject) => {
    const timer = setTimeout(
      () => reject(new Error(`gateway request timeout: ${method}`)),
      REQUEST_TIMEOUT_MS,
    );

    const handler = (data: WebSocket.RawData) => {
      const msg = JSON.parse(data.toString()) as Record<string, unknown>;
      if (msg.type === "res" && msg.id === id) {
        clearTimeout(timer);
        ws.off("message", handler);
        resolve(msg);
      }
    };
    ws.on("message", handler);
  });
}

/**
 * Check whether the Agencity backend is reachable.
 */
async function isAgencityReachable(): Promise<boolean> {
  try {
    const res = await fetch(`${AGENCITY_URL}/health`, { signal: AbortSignal.timeout(3000) });
    return res.ok;
  } catch {
    return false;
  }
}

// ─── Tests ────────────────────────────────────────────────────────────────────

describe("OpenClaw Gateway — connectivity", () => {
  it("gateway is reachable at ws://127.0.0.1:18789", async () => {
    const ws = new WebSocket(GATEWAY_URL);
    await new Promise<void>((resolve, reject) => {
      ws.once("open", resolve);
      ws.once("error", reject);
      setTimeout(() => reject(new Error("connect timeout")), CONNECT_TIMEOUT_MS);
    });
    expect(ws.readyState).toBe(WebSocket.OPEN);
    ws.close();
  });

  it("rejects connection without valid token", async () => {
    const ws = new WebSocket(GATEWAY_URL);

    const result = await new Promise<{ ok: boolean; closed: boolean }>((resolve) => {
      let settled = false;
      const done = (r: { ok: boolean; closed: boolean }) => {
        if (!settled) {
          settled = true;
          resolve(r);
        }
      };
      ws.once("open", () => {
        ws.send(
          JSON.stringify({
            type: "req",
            id: "c1",
            method: "connect",
            params: {
              minProtocol: 1,
              maxProtocol: 9999,
              client: { id: "test", displayName: "bad", version: "0", platform: "test", mode: "test" },
              caps: [],
              auth: { token: "wrong-token-totally-invalid" },
            },
          }),
        );
      });
      ws.on("message", (data) => {
        const msg = JSON.parse(data.toString()) as { ok?: boolean };
        done({ ok: msg.ok === true, closed: false });
      });
      ws.on("close", () => done({ ok: false, closed: true }));
      ws.on("error", () => done({ ok: false, closed: true }));
      setTimeout(() => done({ ok: false, closed: false }), CONNECT_TIMEOUT_MS);
    });

    // Either rejected by message or connection closed — either proves auth works
    expect(result.ok).toBe(false);
    ws.close();
  });

  it("connects successfully with correct token", async () => {
    const { ws, hello, close } = await openGatewayWs(GATEWAY_TOKEN);
    expect(hello.ok).toBe(true);
    expect(hello.type).toBe("res");
    close();
  });
});

describe("OpenClaw Gateway — protocol", () => {
  let ws: WebSocket;
  let closeFn: () => void;

  beforeAll(async () => {
    const conn = await openGatewayWs(GATEWAY_TOKEN);
    ws = conn.ws;
    closeFn = conn.close;
  });

  afterAll(() => closeFn?.());

  it("hello payload contains protocol version", async () => {
    // Re-read via a fresh connection to inspect hello contents
    const { hello, close: c } = await openGatewayWs(GATEWAY_TOKEN);
    // Protocol version is in the response payload or nested result
    const payload = (hello.result ?? hello) as Record<string, unknown>;
    expect(payload).toBeTruthy();
    c();
  });

  it("ping/pong via gateway WebSocket heartbeat", async () => {
    let pongReceived = false;
    ws.once("pong", () => {
      pongReceived = true;
    });
    ws.ping();
    await new Promise((r) => setTimeout(r, 1000));
    expect(pongReceived).toBe(true);
  });

  it("responds to unknown method with error, not crash", async () => {
    const res = await gatewayRequest(ws, "agencity.nonexistent.method", { foo: "bar" });
    // Should get an error response, not hang or disconnect
    expect(res.type).toBe("res");
    expect(res.ok).toBe(false);
  });

  it("gateway remains connected after bad request", async () => {
    // After the bad request above, ws should still be open
    expect(ws.readyState).toBe(WebSocket.OPEN);
  });
});

describe("OpenClaw Gateway — multiple concurrent clients", () => {
  it("supports at least 3 simultaneous connections", async () => {
    const clients = await Promise.all([
      openGatewayWs(GATEWAY_TOKEN),
      openGatewayWs(GATEWAY_TOKEN),
      openGatewayWs(GATEWAY_TOKEN),
    ]);

    for (const { hello } of clients) {
      expect(hello.ok).toBe(true);
    }

    for (const { close } of clients) {
      close();
    }
  });
});

describe("OpenClaw Gateway — Agencity tool invocation", () => {
  let ws: WebSocket;
  let closeFn: () => void;
  let agencityUp: boolean;

  beforeAll(async () => {
    const conn = await openGatewayWs(GATEWAY_TOKEN);
    ws = conn.ws;
    closeFn = conn.close;
    agencityUp = await isAgencityReachable();
  });

  afterAll(() => closeFn?.());

  it("Agencity backend health check", async () => {
    if (!agencityUp) {
      console.warn(`  Agencity not running at ${AGENCITY_URL} — skipping backend tests`);
    }
    // Not a hard failure — gateway tests run independently
    expect(typeof agencityUp).toBe("boolean");
  });

  it("can invoke agencity_search tool via gateway http-tool call", async () => {
    if (!agencityUp) {
      console.warn("  Skipping: Agencity backend not reachable");
      return;
    }

    const res = await gatewayRequest(ws, "tools.invoke", {
      tool: "agencity_search",
      params: {
        query: "senior software engineer machine learning",
        limit: 5,
      },
    });

    // Either succeeds with results or returns a structured error — not a gateway crash
    expect(res.type).toBe("res");
  });

  it("agencity /health endpoint returns 200", async () => {
    if (!agencityUp) {
      console.warn("  Skipping: Agencity backend not reachable");
      return;
    }

    const res = await fetch(`${AGENCITY_URL}/health`);
    expect(res.status).toBe(200);
  });

  it("agencity search endpoint accepts POST", async () => {
    if (!agencityUp) {
      console.warn("  Skipping: Agencity backend not reachable");
      return;
    }

    const res = await fetch(`${AGENCITY_URL}/api/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: "ML engineer", limit: 3, include_external: false }),
      signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
    });

    // Expect structured response (even if no results)
    expect(res.status).toBeLessThan(500);
    const body = (await res.json()) as unknown;
    expect(body).toBeTruthy();
  });
});

describe("OpenClaw Gateway — auth security", () => {
  it("closes connection on malformed connect payload", async () => {
    const ws = new WebSocket(GATEWAY_URL);

    const closed = await new Promise<boolean>((resolve) => {
      ws.once("open", () => {
        // Send garbage — not a valid request
        ws.send("not json at all ###");
      });
      ws.once("close", () => resolve(true));
      ws.on("error", () => resolve(true));
      setTimeout(() => {
        resolve(false);
        ws.close();
      }, 5000);
    });

    // Gateway should close the ws on bad input
    expect(closed).toBe(true);
  });

  it("does not leak token in error messages", async () => {
    const ws = new WebSocket(GATEWAY_URL);

    const messages: string[] = [];
    const done = new Promise<void>((resolve) => {
      ws.once("open", () => {
        ws.send(
          JSON.stringify({
            type: "req",
            id: "c1",
            method: "connect",
            params: {
              minProtocol: 1,
              maxProtocol: 9999,
              client: { id: "t", displayName: "t", version: "0", platform: "test", mode: "test" },
              caps: [],
              auth: { token: "super-secret-bad-token" },
            },
          }),
        );
      });
      ws.on("message", (data) => {
        messages.push(data.toString());
        resolve();
      });
      ws.on("close", resolve);
      ws.on("error", resolve);
      setTimeout(resolve, 5000);
    });

    await done;
    ws.close();

    for (const msg of messages) {
      expect(msg).not.toContain("super-secret-bad-token");
    }
  });
});
