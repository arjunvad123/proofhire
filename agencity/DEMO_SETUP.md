# Demo Setup - Confido

This demo is pre-configured to use the **Confido** company profile.

## Automatic Setup

The application now automatically initializes with Confido's company data on first load. You don't need to complete the onboarding flow.

### What's Pre-Configured

- **Company**: Confido (confidotech.com)
- **Industry**: Fintech
- **Network Size**: 3,637 connections
- **Active Roles**: 5 roles (Software Engineer, Founding Growth, Head of Finance, etc.)
- **Tech Stack**: Python, React, AI/ML, PostgreSQL

## How It Works

1. The `DemoInitializer` component runs on app load
2. It checks if localStorage has onboarding data
3. If not, it automatically sets up Confido's company data
4. All pages (Company, Search, etc.) will now work immediately

## Manual Setup (if needed)

If you need to manually reset or configure the demo:

### Option 1: Browser Console
Open the browser console and run:
```javascript
// Load the init script
fetch('/init-demo.js').then(r => r.text()).then(eval);
```

### Option 2: Direct localStorage
```javascript
localStorage.clear();
// Then refresh the page to trigger auto-initialization
```

### Option 3: Clear and Re-initialize
```javascript
localStorage.removeItem('onboarding-state');
window.location.reload();
```

## Company ID

Confido Company ID: `100b5ac1-1912-4970-a378-04d0169fd597`

## Testing the Demo

1. Navigate to http://localhost:3000/dashboard
2. Visit Company Page - should show Confido details
3. Visit Search Page - should allow searching across the network
4. Visit Candidates Page - should show candidate curation

## Troubleshooting

If you see "Please complete onboarding first":

1. Check browser console for initialization logs
2. Check localStorage in DevTools (Application → Local Storage)
3. Manually run the initialization script from `/init-demo.js`
4. Ensure backend is running on port 8001

## Backend Status

Verify backend is running:
```bash
curl http://localhost:8001/health
```

Should return:
```json
{
  "status": "healthy",
  "environment": "development"
}
```
