# Next Steps & Known Issues

## Current Status

✅ **Working**: Live data via Organillero API + Playwright + GitHub Actions
✅ **Working**: Auto-refresh every 30s in browser
✅ **Working**: Fallback to sample data if live unavailable
✅ **Working**: Auto-select Line 1 on page load

## Known Failures & Blockers

### 1. CORS Blocking Direct Browser Fetch

**Problem**: Organillero API has no CORS headers
- Direct `fetch()` from browser → blocked by CORS policy
- CORS proxies (`allorigins.win`, `corsproxy.io`) → fail or return empty

**Current Workaround**: 
- GitHub Action runs Playwright on Ubuntu VM
- Playwright navigates to Organillero site (establishes origin context)
- Fetches data, commits to repo as `data/live_vehicles.json`
- Browser loads pre-fetched static file (no CORS issue)

**Limitation**: Data only updates every 5 minutes (GitHub Action schedule), not true real-time in browser

### 2. Metrobús Official API - Not Yet Understood

**Status**: ⚠️ **PENDING INVESTIGATION**

**What We Know**:
- Registration at https://metrobus.cdmx.gob.mx/portal-ciudadano/datos-abiertos
- Email provides temporary S3 signed URLs (12-hour expiry)
- Format: Protocol Buffer binary (`.proto` files)
- Three feeds: vehicle positions, trip updates, alerts

**What We Don't Know**:
- How to get permanent API credentials (not 12-hour temp URLs)
- Whether permanent endpoint exists for production use
- API rate limits, authentication method
- How to request developer access vs. one-time download

**Why This Matters**:
- Would eliminate dependency on third-party Organillero API
- Official source = more reliable, potentially better data quality
- Could enable true browser-based real-time updates if CORS-enabled

### 3. Pyodide/WASM Limitations

**Problem**: Cannot run Playwright in browser
- Playwright requires native OS (Chrome binary, system libraries)
- Pyodide = Python WASM, no access to system processes
- Browser security model prevents spawning browser instances

**Impact**: Must rely on backend (GitHub Actions) for CORS bypass

## Next Steps

### Priority 1: Understand Metrobús Official API

**Actions**:
1. [ ] Re-register at Metrobús portal, carefully read email instructions
2. [ ] Check if permanent API keys available (contact support if needed)
3. [ ] Test S3 URLs: check CORS headers, expiry behavior
4. [ ] Document actual API structure vs. documentation
5. [ ] Investigate if `datosabiertos.metropolitanos.mx` will ever work (currently NXDOMAIN)

**Questions to Answer**:
- Is there a permanent endpoint for developers?
- Can we request long-lived credentials?
- Does official API have CORS headers?
- What's the update frequency?

### Priority 2: Optimize Current Solution

**Actions**:
1. [ ] Test GitHub Action reliability (does it actually run every 5min?)
2. [ ] Add error handling if Organillero API goes down
3. [ ] Monitor Action quota (2000 min/month free tier)
4. [ ] Consider reducing frequency to every 10-15min to conserve quota
5. [ ] Add timestamp display showing data freshness

### Priority 3: Explore Alternative Architectures

**Options to Investigate**:

**A. Serverless Function Proxy**
- Deploy simple CORS proxy on Vercel/Netlify/Cloudflare Workers
- Function fetches Organillero, adds CORS headers
- Browser calls our proxy → true real-time
- Cost: Free tier likely sufficient

**B. WebSocket/SSE Stream**
- Backend service maintains connection to data source
- Streams updates to browser clients
- More complex, requires persistent backend

**C. Browser Extension**
- Extension has elevated permissions (no CORS)
- Could fetch directly from Organillero
- Limited audience (requires install)

### Priority 4: Data Quality & Features

**Actions**:
1. [ ] Compare Organillero data vs. official Metrobús data
2. [ ] Validate route_id mappings are correct
3. [ ] Add data quality metrics (missing vehicles, stale timestamps)
4. [ ] Implement vehicle clustering on map
5. [ ] Add historical position tracking

## Technical Debt

1. **Test Coverage**: Add tests for `fetch_organillero.py`
2. **Error Logging**: Better error messages when data fetch fails
3. **Monitoring**: Track GitHub Action success rate
4. **Documentation**: Document Organillero API format/behavior
5. **Cleanup**: Remove unused `test_cors.js` file

## Open Questions

1. Why does Organillero API work without CORS when navigating to site first?
2. Can we contact Organillero maintainer for API documentation?
3. Is there a Metrobús developer community/forum?
4. What's the actual update frequency of official Metrobús feeds?
5. Are there other CDMX transit APIs we should explore?

## Resources

- **Organillero**: https://organillero.heliouz.com
- **Metrobús Datos Abiertos**: https://metrobus.cdmx.gob.mx/portal-ciudadano/datos-abiertos
- **GTFS-RT Spec**: https://gtfs.org/realtime/
- **Current Implementation**: See `scripts/fetch_organillero.py` and `.github/workflows/update-live-data.yml`

---

**Last Updated**: 2026-05-13
**Status**: Functional but dependent on third-party API
**Priority**: Investigate official Metrobús API access
