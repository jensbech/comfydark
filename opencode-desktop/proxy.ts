const PORT = Number(process.env.PORT ?? 1234);
const HOSTNAME = process.env.HOSTNAME ?? "0.0.0.0";
const UPSTREAM_HOST = process.env.UPSTREAM_HOST ?? "127.0.0.1";
const UPSTREAM_PORT = Number(process.env.UPSTREAM_PORT ?? 4096);
const UPSTREAM_HTTP = `http://${UPSTREAM_HOST}:${UPSTREAM_PORT}`;
const UPSTREAM_WS = `ws://${UPSTREAM_HOST}:${UPSTREAM_PORT}`;
const OVERRIDE_ID = process.env.OVERRIDE_ID ?? "amoled";
const THEME_FILE = process.env.THEME_FILE
  ?? new URL("./comfydark.json", import.meta.url).pathname;

const themeRe = new RegExp(`^/assets/${OVERRIDE_ID}-[^/]+\\.js$`);

const HOP_BY_HOP = new Set([
  "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
  "te", "trailers", "transfer-encoding", "upgrade", "host",
]);

function stripHopByHop(h: Headers): Headers {
  const out = new Headers();
  for (const [k, v] of h) if (!HOP_BY_HOP.has(k.toLowerCase())) out.set(k, v);
  return out;
}

async function buildThemeModule(): Promise<string> {
  const json = JSON.parse(await Bun.file(THEME_FILE).text());
  return `export default ${JSON.stringify(json)};`;
}

type WsData = { upstream: WebSocket; queue: (string | Buffer | ArrayBuffer)[]; ready: boolean };

const server = Bun.serve<WsData>({
  port: PORT,
  hostname: HOSTNAME,
  idleTimeout: 0,

  async fetch(req, server) {
    const url = new URL(req.url);

    if (themeRe.test(url.pathname)) {
      try {
        const body = await buildThemeModule();
        return new Response(body, {
          headers: {
            "Content-Type": "application/javascript; charset=utf-8",
            "Cache-Control": "no-cache",
          },
        });
      } catch (err) {
        return new Response(`theme load failed: ${err}`, { status: 500 });
      }
    }

    if (req.headers.get("upgrade")?.toLowerCase() === "websocket") {
      const upstream = new WebSocket(UPSTREAM_WS + url.pathname + url.search);
      const data: WsData = { upstream, queue: [], ready: false };
      if (server.upgrade(req, { data })) return;
      return new Response("upgrade failed", { status: 500 });
    }

    const target = UPSTREAM_HTTP + url.pathname + url.search;
    const upstreamReqHeaders = stripHopByHop(req.headers);
    upstreamReqHeaders.delete("accept-encoding");
    const upstreamRes = await fetch(target, {
      method: req.method,
      headers: upstreamReqHeaders,
      body: req.body,
      redirect: "manual",
    });
    const resHeaders = new Headers(upstreamRes.headers);
    resHeaders.delete("content-encoding");
    resHeaders.delete("content-length");
    resHeaders.delete("transfer-encoding");
    return new Response(upstreamRes.body, {
      status: upstreamRes.status,
      statusText: upstreamRes.statusText,
      headers: resHeaders,
    });
  },

  websocket: {
    open(ws) {
      const { upstream } = ws.data;
      upstream.binaryType = "arraybuffer";
      upstream.addEventListener("open", () => {
        ws.data.ready = true;
        for (const m of ws.data.queue) upstream.send(m as any);
        ws.data.queue = [];
      });
      upstream.addEventListener("message", (e) => ws.send(e.data));
      upstream.addEventListener("close", (e) => ws.close(e.code, e.reason));
      upstream.addEventListener("error", () => ws.close(1011, "upstream error"));
    },
    message(ws, msg) {
      if (ws.data.ready) ws.data.upstream.send(msg as any);
      else ws.data.queue.push(msg);
    },
    close(ws) {
      try { ws.data.upstream.close(); } catch {}
    },
  },
});

console.log(`opencode-proxy listening on ${HOSTNAME}:${PORT} -> ${UPSTREAM_HTTP}`);
console.log(`override: /assets/${OVERRIDE_ID}-*.js -> ${THEME_FILE}`);
