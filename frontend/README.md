# Fr8Labs Outlook Add-in (v2)

Production-grade **frontend-only** Outlook add-in: three ribbon buttons, React + TypeScript + Vite, mocked services ready for backend integration.

## Prerequisites

- Node.js 20+
- Outlook on the web or Outlook desktop (Microsoft 365)
- HTTPS dev certificates: `npm run certs`

## Local development

```bash
cd frontend
npm install
npm run certs    # once — trusts https://localhost
npm run dev      # https://localhost:3000
```

## Sideload for testing

1. Keep `npm run dev` running.
2. Outlook Web → **Settings** → **Add-ins** → **My add-ins**.
3. **+ Add a custom add-in** → **Add from file**.
4. Select [`manifest.xml`](manifest.xml).
5. Open a **received email** (read view, not compose).
6. Use ribbon buttons **Draft Reply**, **Create Quote**, **Customer** (or **Apps** menu on some OWA builds).

### Keep the task pane open (recommended)

Outlook **cannot** auto-open an add-in on every email — that is a platform limitation. The best workflow:

1. Open the add-in once (**Apps** → **Fr8Labs Assistant** → **Draft Reply**).
2. Click the **pin** icon at the top of the task pane.
3. The pane stays open as you switch emails; content refreshes automatically.

Re-sideload `manifest.xml` after manifest changes so pinning is enabled.

Validate manifest:

```bash
npm run validate
```

## Build for deployment

```bash
npm run build
```

Output is in `dist/`. Deploy to Replit, Netlify, or any static HTTPS host.

Update every `https://localhost:3000` URL in `manifest.xml` and `AppDomains` to your production URL, then re-upload the manifest.

## Three buttons

| Ribbon button | Task pane view | Behavior |
|---|---|---|
| Draft Reply | `?view=draft` | Generate mock draft → edit → insert into Outlook reply |
| Create Quote | `?view=quote` | Parse/build quote → review → Accept / Edit / Reject |
| Customer | `?view=customer` | Lookup sender → profile or create form |

**Permissions:** `ReadWriteItem` is required for `displayReplyForm` (insert draft into reply). All other actions are propose/review only — nothing auto-sends.

## Wiring up the real backend later

Change **only** these files:

| File | Replace with |
|---|---|
| [`src/auth.ts`](src/auth.ts) | Real Office SSO token passed to backend |
| [`src/services/draftReplyService.ts`](src/services/draftReplyService.ts) | `POST /draft-reply` |
| [`src/services/quoteService.ts`](src/services/quoteService.ts) | `POST /create-quote` + approve endpoint |
| [`src/services/customerService.ts`](src/services/customerService.ts) | `GET /verify-customer`, `POST /create-customer` |

Each service already exports typed interfaces in [`src/types/index.ts`](src/types/index.ts). UI components do not need changes if request/response shapes match.

**No API keys in this repo.** Real secrets belong on the backend only.

## Security notes

- No `localStorage` / `sessionStorage` for tokens or customer data.
- Email content is sanitized before display and before service calls.
- No inline scripts — CSP-friendly Vite bundle.

## Project structure

```
frontend/
  manifest.xml
  index.html              # task pane entry
  commands.html           # ribbon function file
  src/
    App.tsx
    auth.ts
    services/             # mock → real API swap point
    components/           # DraftReply, Quote, Customer panels
    hooks/useEmailItem.ts
    styles/taskpane.css
  public/assets/          # icons 16/32/80
```
