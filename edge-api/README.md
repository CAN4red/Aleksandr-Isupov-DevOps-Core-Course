# Edge API - Cloudflare Workers

A serverless HTTP API deployed on Cloudflare's global edge network.

## Features

- **Multiple Endpoints**: Health check, edge metadata, KV-backed counter
- **Global Distribution**: Automatically runs on 300+ Cloudflare edge locations
- **TypeScript**: Full type safety with Cloudflare Workers types
- **KV Persistence**: Persistent counter using Workers KV
- **Secrets Management**: Secure configuration via Wrangler secrets

## Quick Start

### Prerequisites

- Node.js 18+
- npm
- Cloudflare account

### Installation

```bash
npm install
```

### Development

```bash
npm run dev
```

This starts a local development server with hot reload.

### Deployment

```bash
# Login to Cloudflare (first time only)
npx wrangler login

# Deploy to edge
npm run deploy
```

## Endpoints

| Endpoint | Description |
|----------|-------------|
| `/` | App information and metadata |
| `/health` | Health check |
| `/edge` | Request edge metadata (colo, country, ASN, etc.) |
| `/counter` | KV-backed visit counter |
| `/config` | Configuration overview |
| `/secrets-check` | Verify secrets configuration |

## Configuration

### Environment Variables (wrangler.jsonc)

```jsonc
{
  "vars": {
    "APP_NAME": "edge-api",
    "COURSE_NAME": "devops-core"
  }
}
```

### Secrets

```bash
npx wrangler secret put API_TOKEN
npx wrangler secret put ADMIN_EMAIL
```

### KV Namespace

```bash
# Create namespace
npx wrangler kv namespace create SETTINGS

# Update wrangler.jsonc with the returned ID
```

## Project Structure

```
edge-api/
├── src/
│   └── index.ts      # Main Worker code
├── package.json      # Dependencies and scripts
├── tsconfig.json     # TypeScript configuration
├── wrangler.jsonc    # Worker configuration
├── WORKERS.md        # Lab documentation
└── README.md         # This file
```

## License

MIT
