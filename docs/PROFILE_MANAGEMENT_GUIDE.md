# Profile Management Guide

This guide explains how to manage trading profiles with the new enhanced system.

## Prerequisites

Set the `ADMIN_API_KEY` environment variable:
```bash
export ADMIN_API_KEY=your_admin_key_here
```

## Creating New Profiles

### 1. Basic Profile Creation

```bash
python scripts/admin/create_profile_api.py "Profile Name" "unique_handle" leftCurve
```

### 2. With Custom Parameters

```bash
python scripts/admin/create_profile_api.py "Degen Trader" "degen_001" leftCurve \
  --deposit 500 \
  --risk 0.9 \
  --style degen \
  --assets BTC ETH DOGE
```

### 3. From Template

```bash
python scripts/admin/create_profile_api.py "SCHIZO 2" "schizo_002" schizo \
  --from-template schizo_posters.json \
  --deposit 200
```

## Updating Existing Profiles

### 1. Update Basic Fields

```bash
# Update risk tolerance
python scripts/admin/update_persona_enhanced.py {profile_id} --risk 0.7

# Update bio
python scripts/admin/update_persona_enhanced.py {profile_id} --bio "New bio text"
```

### 2. Load Full Persona from Template

```bash
python scripts/admin/update_persona_enhanced.py {profile_id} \
  --from-json schizo_posters.json
```

### 3. Update via API (Remote)

```bash
python scripts/admin/update_persona_enhanced.py {profile_id} \
  --personality-type leftCurve \
  --api
```

## Managing Persona Data

### 1. Export Account Persona to File

```bash
python scripts/admin/manage_personas.py export {profile_id}
```

### 2. Import Template to Account

```bash
python scripts/admin/manage_personas.py import {profile_id} leftcurve_redacted.json
```

### 3. List All Profiles

```bash
python scripts/admin/manage_personas.py list
```

### 4. Sync All Profiles

```bash
python scripts/admin/manage_personas.py sync
```

## Available Personality Types

- `leftCurve` - High risk, impulsive trader
- `midCurve` - Moderate risk, analytical
- `rightCurve` - Conservative, strategic
- `cynical` - Skeptical, contrarian
- `schizo` - Chaotic, unpredictable

## Available Trading Styles

- `aggressive` - High leverage, frequent trades
- `conservative` - Low leverage, careful entries
- `contrarian` - Goes against the crowd
- `momentum` - Follows trends
- `degen` - YOLO mode

## Persona Templates

Templates are stored in `data/personas/templates/`:

- `leftcurve_redacted.json` - Left curve trader (Drunk Wassie)
- `midcurve_midwit.json` - Mid curve trader (Midwit McGee)
- `rightcurve_bigbrain.json` - Right curve trader (Wise Chad)
- `schizo_posters.json` - SCHIZO POSTERS
- `cynical_midwit.json` - Cynical trader
- `degen_spartan.json` - Degen Spartan
- `hazmat_cat.json` - CL/Hazmat Cat

## API Endpoints

All endpoints require `X-API-Key` header.

### Create Profile
```
POST /api/admin/profiles
```

### Update Persona
```
PATCH /api/admin/profiles/{profile_id}/persona
```

### Get Profile Details
```
GET /api/admin/profiles/{profile_id}
```

### Place Order
```
POST /api/admin/profiles/{profile_id}/orders
```

### Get Positions
```
GET /api/admin/profiles/{profile_id}/positions
```

### Get Balance
```
GET /api/admin/profiles/{profile_id}/balance
```

## Deployment

After making changes:

1. Test locally:
   ```bash
   python scripts/run_enhanced_bot.py --interval 60
   ```

2. Deploy to Fly:
   ```bash
   ./deploy.sh
   ```

3. Check deployment:
   ```bash
   fly logs -a risex-trading-bot
   ```