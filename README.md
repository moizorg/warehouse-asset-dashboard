# Warehouse Asset Management Dashboard

A complete local-network prototype for registering and viewing warehouse assets. It uses a React frontend, Flask REST API, and SQLite, with photograph files stored outside the database.

The interface uses a responsive dark warehouse-control theme inspired by modern operations dashboards: deep navy surfaces, dark burnt-orange accents, compact live metrics, glass-style panels, hover feedback, fixed desktop navigation, and a mobile bottom navigation bar.

The dashboard list intentionally keeps a stable non-hovering table presentation. Interactive hover styling is retained for individual asset-detail surfaces and controls. 

The dashboard footer includes a responsive category distribution chart that totals Asset IDs by category across the current search/filter result. Hovering or clicking a chart segment shows its category, ID count, and percentage.

## Technology stack

- React 19 with Vite and standard responsive CSS
- Python 3.12 with Flask
- SQLite
- Flask-CORS
- Pytest

React and Flask were chosen to keep the prototype lightweight and easy to run on a single warehouse computer.

## Architecture

```text
Browser
  |
  | REST / JSON and multipart image upload
  v
React frontend -> Flask routes/controllers -> Asset services -> SQLite database
                                       |
                                       +-> Dedicated uploads directory
```

The backend keeps HTTP handling in `app/routes`, validation and file handling in `app/services.py`, and SQLite access in `app/database.py`. This separation allows future barcode, RFID, IoT, ERP, authentication, or API-key integrations to reuse domain services.

## Database schema

Table: `assets`

| Column | Type | Constraints |
|---|---|---|
| id | INTEGER | Primary key, autoincrement |
| asset_identifier | TEXT | Not null, unique, case-insensitive |
| category | TEXT | Not null |
| photograph_path | TEXT | Not null |
| created_at | TEXT | Not null, UTC SQLite timestamp |

Indexes exist for `asset_identifier` and `category`. Images are kept in `backend/uploads/` and SQLite stores their relative path.

## API documentation

### Create an asset

`POST /api/assets`

Multipart fields:

- `asset_identifier` - required, trimmed, 1-64 characters
- `category` - required
- `photograph` - required PNG, JPG, or JPEG, maximum 5 MB

```bash
curl -F "asset_identifier=WH-MCH-001" -F "category=Machinery" -F "photograph=@photo.jpg" http://localhost:5000/api/assets
```

Status codes: `201` created, `400` validation error, `409` duplicate Asset ID, `413` file too large.

### List assets

`GET /api/assets?search=asset123&page=1&limit=10`

Search is case-insensitive. Response includes `items` and pagination metadata.

### Fetch one asset

`GET /api/assets/:id`

### Fetch photograph

`GET /api/assets/:id/photograph`

Returns the stored image.

Error responses use JSON: `{ "error": "Description" }`.

## Setup

### Prerequisites

- Python 3.12+
- Node.js 20+ and npm

### Backend

Windows PowerShell:

```powershell
cd C:\warehouse-asset-dashboard\backend
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python app.py
```

The backend listens on `0.0.0.0:5000`. The database and uploads directories are created automatically. Seed sample records:

```powershell
python seed.py
```

The seed script replaces demo asset records with 30 assets across the six named categories in a deterministic randomized order. Each category has five Asset IDs, and repeated cars, furniture, hammers, laptops, machines, and PPE receive different hue, saturation, brightness, and category-tint treatments while retaining the original composition.

### Frontend

In another terminal:

```powershell
cd C:\warehouse-asset-dashboard\frontend
npm install
Copy-Item .env.example .env
npm run dev
```

Open `http://localhost:5173`.

### Vercel deployment

**Live production deployment:** [https://warehouse-asset-dashboard.vercel.app](https://warehouse-asset-dashboard.vercel.app)

The production dashboard is deployed on Vercel and serves the React frontend with the Flask REST API from the same origin. The deployment exposes the seeded asset dashboard, search and pagination, photograph endpoints, asset details, and category distribution chart.

The repository includes a Vercel configuration for a single-origin deployment:

```powershell
vercel login
vercel
vercel --prod
```

Set `VITE_API_BASE_URL=/api` in Vercel's project environment variables. The Python API is exposed through `/api/index`, and Vite serves the React application from the same deployment.

For Vercel, SQLite and uploads use ephemeral `/tmp` storage. Data and photographs can change when serverless instances restart or scale. Use an external SQLite-compatible persistent volume or object storage before production use.

### Docker

```powershell
docker compose up --build
```

Docker volumes persist SQLite and uploaded photographs.

## Environment variables

Backend:

| Variable | Default | Purpose |
|---|---|---|
| HOST | `0.0.0.0` | Network bind address |
| PORT | `5000` | Backend port |
| DATABASE_PATH | `./data/assets.db` | SQLite file location |
| UPLOAD_FOLDER | `./uploads` | Stored photograph directory |
| ALLOWED_ORIGINS | localhost Vite origins | CORS allowlist |

Frontend:

| Variable | Default | Purpose |
|---|---|---|
| VITE_API_BASE_URL | empty (same-origin API calls) | Backend origin, for example `http://192.168.1.25:5000` |

Do not set frontend API URL to `localhost` if phones or other devices will access it. The frontend source never hardcodes an API host.

## Local network access

1. On the warehouse computer, find its IPv4 address:

```powershell
ipconfig
```

Use the address shown under the active Ethernet or Wi-Fi adapter, such as `192.168.1.25`.

2. Start the backend and frontend as shown above.
3. Set `frontend/.env`:

```text
VITE_API_BASE_URL=http://192.168.1.25:5000
```

4. Restart Vite.
5. On a phone or another computer on the same network, open `http://192.168.1.25:5173`.
6. Allow inbound TCP ports `5000` and `5173` through the Windows Firewall for the private network profile.

CORS remains restricted to the origins in `ALLOWED_ORIGINS`. Add approved LAN origins explicitly, for example `http://192.168.1.25:5173`. For persistence, keep `DATABASE_PATH` and `UPLOAD_FOLDER` on a persistent volume or dedicated warehouse drive and back them up.

## Tests

Backend:

```powershell
cd backend
pytest -q
```

Frontend build:

```powershell
cd frontend
npm run build
npm test
```

The backend tests cover database initialization, creation, duplicate rejection, case-insensitive search, individual fetch, invalid file types, oversized files, and API validation.

## Screenshots

Screenshots will be placed in [`docs/screenshots/`](docs/screenshots/):

- `dashboard-desktop.png`
- `dashboard-mobile.png`
- `create-asset.png`
- `create-asset-mobile.png`
- `image-preview.png`
- `asset-detail.png`
- `empty-search.png`

The screenshots demonstrate the dark, responsive operations-dashboard interface, including inventory metrics, photograph thumbnails, image preview, individual asset details, and empty search results.

## Known limitations

- No authentication or role management
- No image replacement or deletion
- No barcode/RFID-specific fields
- SQLite is suitable for a small on-premises prototype, not high-write/high-concurrency production deployment
- Seed photographs are generated demo images only, and production deployment requires real operator photographs
- No antivirus scanning or malware content validation beyond extension, MIME selection, and server-side size checks

## Future integration possibilities

- Barcode and QR scanners
- RFID reader services
- Industrial IoT feed ingestion
- ERP or WMS synchronization
- Bulk uploads and CSV import
- API keys or OAuth
- Authentication and role-based authorization
- Audit history
- Additional asset metadata
- Image replacement and retention policies
