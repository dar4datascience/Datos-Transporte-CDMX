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

### Priority 0: Dashboard Creation & Hosting

**Goal**: Create a dedicated dashboard interface and deploy to a stable hosting platform

#### Dashboard Design

**Current State**: Single-page Quarto document (`index.qmd`) with map + table
**Desired State**: Full-featured dashboard with multiple views and analytics

**Proposed Features**:
1. **Multi-line view**: Show all lines simultaneously with toggle controls
2. **Analytics panel**: 
   - Vehicles per line (bar chart)
   - Average speed by line
   - Historical trends (if data available)
3. **Time controls**: Play/pause historical playback (if storing history)
4. **Alert system**: Show service disruptions from GTFS-RT alerts feed
5. **Mobile optimization**: Responsive layout for mobile users
6. **Search**: Find specific routes/stops

**Technology Options**:

**Option A: Quarto Dashboard (Recommended)**
- Use Quarto's dashboard framework
- Keep current OJS + Pyodide + Leaflet stack
- Add `bslib` components for layout
- Pros: Familiar stack, good documentation
- Cons: Limited to Quarto ecosystem

**Option B: Streamlit**
- Pure Python dashboard framework
- Use `streamlit-folium` for maps
- Pros: Easy to build, Python-native
- Cons: Requires Python backend, not static

**Option C: Shiny (R)**
- R-based dashboard framework
- Use `leaflet` + `bslib` for UI
- Pros: Excellent for data viz, mature ecosystem
- Cons: Requires R backend, not static

**Option D: Custom React/Vue App**
- Modern SPA with React + Leaflet
- Deploy to Vercel/Netlify
- Pros: Full control, modern UX
- Cons: Requires rewrite of current code

#### Hosting Options

**Option 1: Quarto Pub / GitHub Pages (Current)**
- **How it works**: Quarto renders to static HTML, deploy via GitHub Actions
- **Pros**: Free, simple, static (no backend needed)
- **Cons**: Limited to static content, no server-side processing
- **Cost**: Free
- **Setup**: Already configured (`.github/workflows/quarto-publish.yml`)

**Option 2: Vercel / Netlify**
- **How it works**: Deploy static site with CDN
- **Pros**: Fast global CDN, easy deployment, preview deployments
- **Cons**: Still static, no backend
- **Cost**: Free tier generous
- **Setup**: Connect GitHub repo, auto-deploy on push

**Option 3: Streamlit Cloud / Shinyapps.io**
- **How it works**: Host Python/R backend with dashboard
- **Pros**: Can run server-side code, true real-time updates
- **Cons**: Requires backend, not free at scale
- **Cost**: Free tier limited, paid tiers for production
- **Setup**: Deploy app to cloud platform

**Option 4: Custom Backend (VPS/Cloud)**
- **How it works**: Deploy Flask/FastAPI + frontend separately
- **Pros**: Full control, can run any backend logic
- **Cons**: Maintenance overhead, security concerns
- **Cost**: $5-20/month for basic VPS
- **Setup**: Configure server, SSL, monitoring

**Recommendation**: Start with **Quarto Pub / GitHub Pages** (current) for MVP. If dashboard needs server-side features, migrate to **Vercel + serverless function** for CORS proxy.

#### Simplifying Live Data Fetching

**Current Complexity**:
- GitHub Action runs Playwright every 5 minutes
- Playwright fetches Organillero data (bypasses CORS)
- Commits JSON to repo
- Browser loads pre-fetched static file
- Data latency: 5 minutes (not true real-time)

**Simplification Options**:

**Option A: Serverless CORS Proxy (Recommended)**
- Deploy Cloudflare Worker / Vercel Function
- Function: `fetch(organillero) → add CORS headers → return`
- Browser calls our proxy directly
- **Pros**: True real-time (30s updates), simple architecture
- **Cons**: Need to deploy function
- **Cost**: Free tier sufficient
- **Implementation**: ~50 lines of code

```javascript
// Cloudflare Worker example
export default {
  async fetch(request) {
    const response = await fetch('https://organillero.heliouz.com/api/realtime');
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET',
    };
    return new Response(response.body, {
      headers: { ...response.headers, ...corsHeaders }
    });
  }
};
```

**Option B: Contact Organillero for CORS**
- Reach out to Heliouz (Organillero maintainer)
- Request CORS headers be added to API
- **Pros**: No infrastructure needed, cleanest solution
- **Cons**: Depends on third-party cooperation
- **Cost**: Free
- **Action**: Email contact@heliouz.com

**Option C: Use Metrobús Official API (If CORS-enabled)**
- Investigate if official API has CORS
- May need to request developer credentials
- **Pros**: Official source, more reliable
- **Cons**: Unclear if CORS-enabled, unclear access process
- **Cost**: Free (if access granted)

**Option D: Accept 5-minute latency**
- Keep current GitHub Action approach
- Optimize Action to run faster
- **Pros**: Works now, no changes needed
- **Cons**: Not true real-time, data stale
- **Cost**: Free
- **Status**: Current solution

**Recommendation**: Try **Option B** (contact Organillero) first. If unsuccessful, implement **Option A** (serverless proxy). Both enable true real-time data without complex Playwright setup.

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
