# How to Update Sample GTFS-RT Data

This guide explains how to refresh the sample vehicle data with a new snapshot from Metrobús.

## Background

Metrobús provides GTFS-RT data via **temporary S3 signed URLs** that expire after 12 hours. The registration email contains a download link that looks like:

```
https://sonda-gtfs-prd.s3.amazonaws.com/1339/Metrobus_GTFS_RT.proto?X-Amz-Security-Token=...
```

## Step-by-Step Update Process

### 1. Request Fresh Download Link

Go to the [Metrobús Datos Abiertos portal](https://metrobus.cdmx.gob.mx/portal-ciudadano/datos-abiertos) and request access again, or check your email for an existing valid link (valid for 12 hours).

### 2. Copy the S3 URL

From the email, copy the full URL for "Datos abiertos de Metrobús Realtime". It should start with:
```
https://sonda-gtfs-prd.s3.amazonaws.com/1339/Metrobus_GTFS_RT.proto?...
```

### 3. Download Fresh Binary

```bash
cd /path/to/Datos-Transporte-CDMX

# Replace [URL] with the actual S3 URL from email
curl -o Metrobus_GTFS_RT.proto "[PASTE-S3-URL-HERE]"
```

**Example**:
```bash
curl -o Metrobus_GTFS_RT.proto "https://sonda-gtfs-prd.s3.amazonaws.com/1339/Metrobus_GTFS_RT.proto?X-Amz-Security-Token=IQoJb3..."
```

### 4. Parse to JSON

```bash
python scripts/parse_sample_gtfs_rt.py Metrobus_GTFS_RT.proto data/sample_vehicles.json
```

**Expected output**:
```
✅ Extracted 810 vehicles from GTFS-RT feed
📅 Feed timestamp: 2026-05-13T18:53:53
💾 Saved to: data/sample_vehicles.json

📊 Sample vehicle:
{
  "vehicle_id": "69379",
  "route_id": "19471",
  "latitude": 19.505024,
  "longitude": -99.189568,
  "timestamp": 1778720030,
  "speed": 45.0,
  "bearing": 100.0
}
```

### 5. Verify the Update

```bash
# Check timestamp
python -c "import json; data = json.load(open('data/sample_vehicles.json')); print(f'Timestamp: {data[\"feed_timestamp_iso\"]}'); print(f'Total vehicles: {data[\"total_vehicles\"]}')"

# Preview in browser
quarto preview index.qmd
```

### 6. Commit Changes

```bash
git add data/sample_vehicles.json Metrobus_GTFS_RT.proto
git commit -m "Update sample GTFS-RT data - $(date +%Y-%m-%d)"
git push
```

## Automation Considerations

### Why Not Automate?

- URLs expire after 12 hours
- No permanent API endpoint
- Requires manual email request
- GitHub Actions can't access temporary URLs

### Possible Solutions

1. **Contact Metrobús** - Request permanent API credentials for automated access
2. **Scheduled Manual Updates** - Update sample data weekly/monthly as needed
3. **User-Provided URLs** - Add UI for users to paste their own temporary URLs

## Troubleshooting

### URL Expired (403 Error)

```bash
curl -I "https://sonda-gtfs-prd.s3.amazonaws.com/..."
# HTTP/1.1 403 Forbidden
```

**Solution**: Request a new download link from the registration portal.

### Parse Error

```
Exception: Failed to parse GTFS-RT data
```

**Solution**: Verify the downloaded file is valid:
```bash
file Metrobus_GTFS_RT.proto
# Should show: Metrobus_GTFS_RT.proto: data
```

### No Vehicles Extracted

```
✅ Extracted 0 vehicles from GTFS-RT feed
```

**Solution**: The feed might be empty or corrupted. Try downloading again with a fresh URL.

## File Structure

```
Datos-Transporte-CDMX/
├── Metrobus_GTFS_RT.proto          # Binary GTFS-RT feed (snapshot)
├── data/
│   └── sample_vehicles.json        # Parsed JSON (used by app)
└── scripts/
    └── parse_sample_gtfs_rt.py     # Parser script
```

## Sample Data Format

`data/sample_vehicles.json`:
```json
{
  "feed_timestamp": 1778720033,
  "feed_timestamp_iso": "2026-05-13T18:53:53",
  "total_vehicles": 810,
  "vehicles": [
    {
      "vehicle_id": "69379",
      "trip_id": null,
      "route_id": "19471",
      "latitude": 19.505024,
      "longitude": -99.189568,
      "timestamp": 1778720030,
      "speed": 45.0,
      "bearing": 100.0
    }
  ]
}
```

## Update Frequency Recommendations

- **Development**: Update when testing new features
- **Production**: Update weekly or when data becomes stale
- **Demonstrations**: Update before presentations/demos

## Questions?

See [GTFS_RT_IMPLEMENTATION.md](GTFS_RT_IMPLEMENTATION.md) for technical details about GTFS-RT parsing.
