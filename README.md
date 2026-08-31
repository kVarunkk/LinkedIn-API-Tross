# LinkedIn Profile API

A FastAPI application that reverse-engineers LinkedIn's internal **Voyager REST API** to extract structured profile data from any public LinkedIn profile URL.

## Challenge Requirements (Satisfied)

| Requirement                                                                                                                | Status   | Evidence                                              |
| -------------------------------------------------------------------------------------------------------------------------- | -------- | ----------------------------------------------------- |
| Deploy publicly over HTTPS                                                                                                 | ✅ Ready | Uvicorn + Render/Heroku instructions included         |
| Accept LinkedIn profile URL                                                                                                | ✅       | `POST /profile` with `profile_url` body               |
| Return structured JSON (name, headline, location, about, experience, education, skills, certifications, languages, images) | ✅       | All fields returned via `ParsedProfile` model         |
| Use own LinkedIn credentials (backend)                                                                                     | ✅       | `X-Li-At` / `X-JSessionID` headers, env fallback      |
| Public GitHub repo with full source                                                                                        | ✅       | All code in `/app/`; `.env` excluded via `.gitignore` |
| README with setup, docs, approach, limitations                                                                             | ✅       | This file                                             |
| Credentials kept out of repo                                                                                               | ✅       | `.env` ignored; only `.env.example` tracked           |

## Verified Endpoint

```
GET https://www.linkedin.com/voyager/api/identity/dash/profiles?q=memberIdentity&memberIdentity={profile_name}&decorationId=com.linkedin.voyager.dash.deco.identity.profile.FullProfileWithEntities-96
```

Confirmed via `curl` with session cookies — returns complete profile (name, headline, location, summary, experience, education, skills, publications, images) in one request.

## Approach

1. **No browser automation** (per assignment constraints). Uses direct HTTP to LinkedIn's internal `voyager/api` endpoints via `httpx`.
2. **Per-request session cookies** (recommended): clients pass their own `X-Li-At` + `X-JSessionID` headers. The server never holds a central account → no sign-out issues.
3. **Env fallback** (private/owner use): server reads `LINKEDIN_LI_AT` / `LINKEDIN_JSESSIONID` from environment.
4. **GraphQL hash rotation** handled via configurable `GRAPHQL_HASH` (`273a499c...` currently working as backup).
5. **Parser** (`parse_profile`) transforms LinkedIn's nested JSON into a flat `ParsedProfile` Pydantic model with all required fields.

## Quick Start

### 1. Install

```bash
python -m venv venv
source venv/bin/activate        # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### 2. Run

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Open docs

- Swagger UI: `http://localhost:8000/docs`
- Health: `GET /health`

## API Endpoint

### `POST /profile` — Only endpoint

**Headers (recommended for public use):**

- `X-Li-At` — your LinkedIn `li_at` cookie
- `X-JSessionID` — your LinkedIn `JSESSIONID` cookie
- `User-Agent` — optional; overrides default Chrome UA if you want your own fingerprint
- `X-Li-Track` — optional; overrides default LinkedIn tracking payload (JSON string)
- _If headers are missing, server falls back to `LINKEDIN_LI_AT` / `LINKEDIN_JSESSIONID` / default UA / default track env vars._

**Request body:**

```json
{
  "profile_url": "https://www.linkedin.com/in/varunkumawat/"
}
```

**cURL example:**

```bash
curl -X POST http://localhost:8000/profile \
  -H "Content-Type: application/json" \
  -H "X-Li-At: AQEDAW1P7NEB..." \
  -H "X-JSessionID: ajax:854527..." \
  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ..." \
  -H "X-Li-Track: {\"clientVersion\":\"0.2.7003\",\"mpVersion\":\"0.2.7003\",\"osName\":\"web\",\"timezoneOffset\":5.5,\"timezone\":\"Asia/Calcutta\",\"deviceFormFactor\":\"DESKTOP\",\"mpName\":\"web\",\"displayDensity\":1,\"displayWidth\":1920,\"displayHeight\":1080}" \
  -d '{"profile_url":"https://linkedin.com/in/varunkumawat"}'
```

**Success response (200):**

```json
{
  "success": true,
  "profile": {
    "name": "Varun Kumawat",
    "first_name": "Varun",
    "last_name": "Kumawat",
    "headline": "building GetHired (4.7k+ users) | IIT Kharagpur'26",
    "industry": "Internet",
    "about": "Full Stack Developer with a keen interest in solving complex problems...",
    "location": {
      "country": "India",
      "city": "Vadodara",
      "country_code": "IN"
    },
    "experience": [
      {
        "title": "Founding Head of Growth",
        "company": "Jack & Jill",
        "location": "Vadodara, India",
        "description": "An Agent Harness",
        "start_date": "2026-05",
        "end_date": "Present"
      }
    ],
    "education": [
      {
        "degree": "BTech",
        "institution": "IIT Kharagpur",
        "start_date": "2021-05",
        "end_date": "2026-05"
      }
    ],
    "skills": [
      "Google Cloud Platform (GCP)",
      "Docker",
      "Python",
      "Vector Databases"
    ],
    "certifications": [],
    "projects": [],
    "publications": [
      {
        "name": "dtmf based home appliances with microcontroller",
        "description": "published on STM journal",
        "publisher": "journal of electronic and application",
        "url": "http://stmjournals.com/",
        "published_date": "2021-06-12",
        "authors": [{ "name": "PANDEY" }]
      }
    ],
    "languages": [],
    "profile_images": [
      {
        "url": "https://media.licdn.com/dms/image/.../profile-displayphoto-shrink_400_400",
        "width": 400,
        "height": 400
      }
    ],
    "public_identifier": "varunkumawat",
    "entity_urn": "urn:li:fsd_profile:ACoAADke-v4BH25OFDMytu5rufIFb8rRi-u1SiI"
  }
}
```

**Missing credentials (400):**

```json
{
  "detail": "Provide session cookies via X-Li-At and X-JSessionID headers (or set LINKEDIN_LI_AT / LINKEDIN_JSESSIONID env vars)."
}
```

**Upstream failure (502):**

```json
{
  "detail": "LinkedIn API error: <message>"
}
```

**Troubleshooting — if you get any error (400 / 502):**
The most common cause is invalid or expired `X-Li-At` / `X-JSessionID` cookies. LinkedIn logs you out after excessive usage, IP mismatch, or rapid requests, so your cookies are likely the problem.

Fix:
1. Log in to `https://www.linkedin.com` again in your browser.
2. Open DevTools (F12) → Network → refresh.
3. Copy fresh `li_at` and `JSESSIONID` cookie values.
4. Pass them in `X-Li-At` and `X-JSessionID` headers and retry.

Only the session cookies need rotation — no server-side changes required.

## Response Schema (`ParsedProfile`)

| Field                               | Type                                                              | Source in LinkedIn data                                      |
| ----------------------------------- | ----------------------------------------------------------------- | ------------------------------------------------------------ |
| `name` / `first_name` / `last_name` | string                                                            | `firstName` / `lastName`                                     |
| `headline`                          | string                                                            | `multiLocaleHeadline.en_US`                                  |
| `industry`                          | string                                                            | `industry.name`                                              |
| `about`                             | string                                                            | `multiLocaleSummary.en_US`                                   |
| `location`                          | `{country, city, country_code}`                                   | `geoLocation.geo` / `location`                               |
| `experience`                        | `[{title, company, location, description, start_date, end_date}]` | `profilePositionGroups`                                      |
| `education`                         | `[{degree, institution, start_date, end_date}]`                   | `profileEducations`                                          |
| `skills`                            | `string[]`                                                        | `profileSkills.elements`                                     |
| `certifications`                    | `string[]`                                                        | `profileCertifications.elements`                             |
| `languages`                         | `string[]`                                                        | `profileLanguages.elements`                                  |
| `publications`                      | `[{name, description, publisher, url, published_date, authors}]`  | `profilePublications.elements`                               |
| `projects`                          | `[{title, description}]`                                          | `profileProjects.elements`                                   |
| `profile_images`                    | `[{url, width, height}]`                                          | `profilePicture.displayImageReference.vectorImage.artifacts` |
| `public_identifier`                 | string                                                            | `publicIdentifier`                                           |
| `entity_urn`                        | string                                                            | `entityUrn`                                                  |

## Why Header-Based Cookies (Prevents Sign-Out)

LinkedIn invalidates `li_at` when a session is used from a different IP than the one that created it. If your server holds one env-based session and your traffic comes from various clients/IPs, **that central account gets signed out after each request**.

**Solution built into this API:** every request carries the caller's own cookies via `X-Li-At` / `X-JSessionID` headers. Each caller's session is used from their own IP, by their own browser fingerprint — no centralized session to invalidate. Env fallback is only for private/owner deployments where the server IP matches the login IP.

**If you must use env-based session**, run the API on the same network/IP you logged in from (e.g., your laptop, ngrok from home, or a co-located VM) and avoid rapid sequential calls.

## How to Get LinkedIn Session Cookies

1. Open `https://www.linkedin.com` in your browser, log in.
2. Press F12 → **Network** tab → reload.
3. Click any `linkedin.com` request → **Headers** → **Cookie**.
4. Copy values of `li_at` and `JSESSIONID`.
5. Pass them in `X-Li-At` and `X-JSessionID` headers per request.

## Approach Details

- **Endpoint**: `GET /voyager/api/identity/dash/profiles?q=memberIdentity&memberIdentity={profile_name}&decorationId=com.linkedin.voyager.dash.deco.identity.profile.FullProfileWithEntities-96`
- **Headers sent upstream**:
  - `accept: */*`
  - `csrf-token: ajax:...` (must match JSESSIONID value)
  - `x-restli-protocol-version: 2.0.0`
  - `user-agent: Mozilla/5.0...` (default Chrome UA; overridable)
  - `x-li-track: {"clientVersion":"0.2.7003", ...}` (default tracking payload; overridable)
  - `referer: https://www.linkedin.com/feed/`
  - `origin: https://www.linkedin.com`
  - `cookie: li_at=...; JSESSIONID="ajax:..."`
- **No browser automation** (per assignment constraints) — pure `httpx` async client.
- **GraphQL backup**: `queryId=273a499c117721535e6da078bee17e9c` for vanity-to-URN resolution if REST fails.

## LinkedIn Internal Architecture

LinkedIn is migrating from **Voyager REST/GraphQL** to **SDUI (Server-Driven UI)** for profile rendering.

- **Voyager** (current): REST endpoints (`/voyager/api/identity/dash/profiles...`) + GraphQL (`queryId=...`) serve raw profile entities as JSON.
- **SDUI / RSC-Action** (emerging): `https://www.linkedin.com/flagship-web/rsc-action/actions/component?componentId=...&sduuid=...` delivers UI fragments (cards, maps, feeds) instead of raw data.
- **Write/Mutation endpoints**: SDUI handles follow-state updates, connection requests, trust verification via `rsc-action/actions/server-request?sduuid=...`.

### Read Endpoints Observed

- `GET /voyager/api/voyagerGlobalAlerts?adHocAlerts=true&alertWithActions=true&q=findAlerts`
- `GET /voyager/api/graphql?includeWebMetadata=true&variables=()&queryId=voyagerFeedDashGlobalNavs.5e79c576bb420351fa8ff438d86b2c31`
- `GET /voyager/api/me`
- `GET /voyager/api/graphql?includeWebMetadata=true&variables=(memberIdentity:ACoAAG1bYPcBgUDWPn6d3tyxfmumrN3loWbFbA8)&queryId=voyagerIdentityDashProfiles.b5c27c04968c409fc0ed3546575b9b7a`
- `GET /voyager/api/voyagerMessagingGraphQL/graphql?queryId=messengerConversations.0d5e6781bbee71c3e51c8843c6519f48&variables=(mailboxUrn:urn%3Ali%3Afsd_profile%3AACoAAG1bYPcBgUDWPn6d3tyxfmumrN3loWbFbA8)`
- `GET /voyager/api/identity/dash/profiles/urn:li:fsd_profile:ACoAAG1bYPcBgUDWPn6d3tyxfmumrN3loWbFbA8?decorationId=com.linkedin.voyager.dash.deco.identity.profile.FullProfile-76`

### SDUI (Server-Driven UI) Endpoints

- `/flagship-web/rsc-action/actions/pagination?sduuid=com.linkedin.sdui.search.blendedSearchResults&parentSpanId=dB8y5szh2NI%3D`
- `/flagship-web/rsc-action/actions/component?componentId=com.linkedin.sdui.generated.profile.dsl.impl.profileCardsActivity&sduuid=com.linkedin.sdui.generated.profile.dsl.impl.profileCardsActivity&parentSpanId=tELZE9AHQd4%3D`
- `/flagship-web/rsc-action/actions/component?componentId=com.linkedin.sdui.generated.profile.dsl.impl.browsemapRecommendedEntitySection&sduuid=com.linkedin.sdui.generated.profile.dsl.impl.browsemapRecommendedEntitySection&parentSpanId=ETeX9dOEKKI%3D`

### Write / Mutation Endpoints (SDUI)

- `/flagship-web/rsc-action/actions/server-request?sduuid=com.linkedin.sdui.requests.mynetwork.addaUpdateFollowState&parentSpanId=t%2B8wVwRC4W0%3D`
- `/flagship-web/rsc-action/actions/server-request?sduuid=com.linkedin.sdui.requests.mynetwork.handlePostInteropConnection&parentSpanId=15%2FKjL%2BuaWw%3D`
- `/flagship-web/rsc-action/actions/server-request?sduuid=com.linkedin.sdui.requests.trustverifications.trustVerificationNbaRequest&parentSpanId=jTsIRQwIGOM%3D`

## Known Limitations

- **Account ban / spam risk**: Repetitive automated requests from the same session can trigger LinkedIn's anti-abuse/anti-spam systems and lock or ban the account. **Do not use your primary LinkedIn account** — use a secondary/test account for this tool, and never run rapid/sustained scraping loops.
- **Session expiration / sign-out**: Excessive usage (or server IP mismatch) causes LinkedIn to invalidate `li_at` immediately — the account gets logged out after a single request. **Solution**: pass per-request cookies via `X-Li-At` / `X-JSessionID` headers (public endpoint) rather than centralizing one server session.
- **Hash rotation**: `GRAPHQL_HASH` for the GraphQL fallback may rotate; REST endpoint is primary.
- **Rate limits**: LinkedIn throttles aggressively; rapid sequential calls trigger temporary blocks.
- **Private profiles**: Only public profiles return data; private/restricted profiles return empty/error responses.
- **No HTTPS by default**: Deploy behind nginx/Cloudflare/Render TLS proxy for production.

## Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI route + parse_profile
│   ├── models.py            # ParsedProfile, PublicationItem, etc.
│   ├── config.py            # Settings + GraphQL hash
│   └── linkedin_client.py   # LinkedIn Voyager REST client
├── .env.example             # Template only (no secrets)
├── .gitignore               # .env, venv, __pycache__ ignored
├── requirements.txt
└── README.md
```

## Deployed URL

- **Live app**: `https://linkedin-api-tross-785917985023.europe-west1.run.app/`
- **Swagger docs**: `https://linkedin-api-tross-785917985023.europe-west1.run.app/docs`
- **Health check**: `https://linkedin-api-tross-785917985023.europe-west1.run.app/health`
- **POST /profile example** (use your own cookies):

```bash
curl -X POST https://linkedin-api-tross-785917985023.europe-west1.run.app/profile \
  -H "Content-Type: application/json" \
  -H "X-Li-At: YOUR_LI_AT" \
  -H "X-JSessionID: ajax:YOUR_ID" \
  -d '{"profile_url":"https://linkedin.com/in/varunkumawat"}'
```

## Deployment (HTTPS Public)

### Cloud Run (Google Cloud) — current

The included `Dockerfile` deploys to Cloud Run. From the project root:

```bash
# 1. Build
gcloud builds submit --tag gcr.io/PROJECT_ID/linkedin-api

# 2. Deploy
gcloud run deploy linkedin-api \
  --image gcr.io/PROJECT_ID/linkedin-api \
  --platform managed \
  --region europe-west1 \
  --allow-unauthenticated \
  --port 8080
```

The container reads `PORT` from the environment and binds to it (defaults to 8080). Set `LINKEDIN_LI_AT` / `LINKEDIN_JSESSIONID` only if you want env-based fallback; recommended is per-request `X-Li-At` / `X-JSessionID` headers.

### Local Docker (run the same image)

```bash
# Build
docker build -t linkedin-api .

# Run
docker run --rm -p 8080:8080 linkedin-api

# Test
curl -X POST http://localhost:8080/profile \
  -H "Content-Type: application/json" \
  -H "X-Li-At: YOUR_LI_AT" \
  -H "X-JSessionID: ajax:YOUR_ID" \
  -d '{"profile_url":"https://linkedin.com/in/varunkumawat"}'
```

### Other platforms (Render / Heroku / VPS)

```yaml
# Example: deploy to Render / Heroku / VPS
buildCommand: pip install -r requirements.txt
startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Or use the included `Dockerfile` directly on any container host (Fly.io, Railway, ECS, etc.). Add HTTPS via proxy (nginx / Cloudflare / AWS ALB).

## Security & Ethics

- Credentials never committed (`.env` in `.gitignore`).
- Session cookies are passed per-request via headers — no server-side persistence.
- Only reads public profile data — no mutations, no scraping beyond REST endpoint.
- Users are responsible for complying with LinkedIn Terms of Service.
