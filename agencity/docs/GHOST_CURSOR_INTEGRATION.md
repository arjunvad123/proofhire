# Ghost Cursor Integration

## Overview

[ghost-cursor](https://www.npmjs.com/package/ghost-cursor) is a Node.js library that creates realistic human-like mouse movements in Playwright. It uses Bezier curves to generate natural, curved mouse paths instead of straight lines.

**Current Status:** ⏸️ Optional Enhancement (Not Required for MVP)

Our current implementation already includes:
- ✅ Random delays between actions
- ✅ Smooth scrolling with multiple steps
- ✅ Curved mouse movement simulation (Python-based)
- ✅ Human behavior patterns

ghost-cursor would provide:
- Even more realistic mouse curves
- Advanced easing functions
- Battle-tested patterns from the community

## Why Ghost Cursor?

### Current Approach (Python)
```python
# app/services/linkedin/human_behavior.py
async def move_to_element_naturally(page, selector):
    box = await element.bounding_box()
    target_x = box['x'] + box['width'] * random.uniform(0.3, 0.7)
    target_y = box['y'] + box['height'] * random.uniform(0.3, 0.7)

    # Simple Bezier-like curve
    for i in range(steps):
        t = i / steps
        curve_factor = 4 * t * (1 - t)
        x = current_x + (target_x - current_x) * t + curve_offset_x
        y = current_y + (target_y - current_y) * t + curve_offset_y
        await page.mouse.move(x, y)
```

### With Ghost Cursor (Node.js)
```javascript
const createCursor = require('ghost-cursor').default;

const cursor = createCursor(page);
await cursor.moveTo({ x: 100, y: 200 });  // Perfect Bezier curves
await cursor.click({ x: 100, y: 200 });
```

## Integration Options

### Option 1: Node.js Subprocess (Simple)

Call ghost-cursor from Python using subprocess:

```python
# app/services/linkedin/ghost_cursor.py

import subprocess
import json
from pathlib import Path

class GhostCursorIntegration:
    """Call ghost-cursor via Node.js subprocess."""

    def __init__(self):
        self.script_path = Path(__file__).parent / 'ghost_cursor_bridge.js'

    async def move_and_click(self, page, selector: str):
        """Move to element and click using ghost-cursor."""
        # Get element position
        box = await page.locator(selector).bounding_box()

        # Call Node.js script
        result = subprocess.run([
            'node',
            str(self.script_path),
            json.dumps({
                'action': 'click',
                'target': {'x': box['x'], 'y': box['y']},
                'cdp_url': page.context._connection.url
            })
        ], capture_output=True, text=True)

        return json.loads(result.stdout)
```

```javascript
// app/services/linkedin/ghost_cursor_bridge.js

const createCursor = require('ghost-cursor').default;
const { chromium } = require('playwright');

async function main() {
    const config = JSON.parse(process.argv[2]);

    // Connect to existing browser via CDP
    const browser = await chromium.connectOverCDP(config.cdp_url);
    const context = browser.contexts()[0];
    const page = context.pages()[0];

    // Create cursor
    const cursor = createCursor(page);

    // Move and click
    await cursor.moveTo(config.target);
    if (config.action === 'click') {
        await cursor.click();
    }

    console.log(JSON.stringify({ success: true }));
    await browser.close();
}

main();
```

**Pros:**
- Simple integration
- Works with existing Python code
- No major refactoring

**Cons:**
- Overhead of subprocess calls
- Need to manage Node.js dependency
- CDP connection complexity

### Option 2: Playwright CDP Bridge (Advanced)

Use Playwright's CDP (Chrome DevTools Protocol) to control mouse from Node.js:

```python
# Connect Python and Node.js via CDP
cdp_url = await page.context._connection.url
```

### Option 3: Stay with Python Implementation (Current - Recommended)

Our current Python implementation is already good enough:
- ✅ Bezier-like curves
- ✅ Random variations
- ✅ Target randomization (not exact center)
- ✅ Natural timing

**When to add ghost-cursor:**
- If accounts still get flagged after testing
- If we need even more realistic patterns
- If community patterns prove more effective

## Installation (If Needed)

```bash
# Install ghost-cursor globally
npm install -g ghost-cursor

# Or in project
cd agencity
npm init -y
npm install ghost-cursor playwright
```

## Testing Ghost Cursor

```javascript
// test_ghost_cursor.js

const { chromium } = require('playwright');
const createCursor = require('ghost-cursor').default;

(async () => {
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();
    const cursor = createCursor(page);

    await page.goto('https://www.linkedin.com/login');

    // Move to email field naturally
    const emailBox = await page.locator('input[name="session_key"]').boundingBox();
    await cursor.moveTo({
        x: emailBox.x + emailBox.width / 2,
        y: emailBox.y + emailBox.height / 2
    });

    // Click
    await cursor.click();

    // Type with delays
    await page.type('input[name="session_key"]', 'test@email.com', { delay: 100 });

    await browser.close();
})();
```

## Performance Comparison

### Current Python Implementation
```
Average mouse movement time: 0.5-1.5s
Steps: 15-30
Pattern: Parabolic curve
Detection risk: Low
```

### Ghost Cursor
```
Average mouse movement time: 0.8-2.0s
Steps: Adaptive (more steps for longer distances)
Pattern: Perfect Bezier with easing
Detection risk: Very Low
```

## Recommendation

**Current Recommendation:** ⏸️ **Wait and Test**

1. **Test current implementation first** (Phase 1-4 from TESTING_GUIDE.md)
2. **Monitor account health** over 7 days
3. **Track warning rates** across multiple test accounts
4. **Only add ghost-cursor if:**
   - Warning rate > 5%
   - Accounts getting flagged repeatedly
   - Current patterns prove insufficient

**Why wait?**
- Current implementation is already sophisticated
- Adding complexity increases maintenance burden
- Need real data to justify the enhancement
- Subprocess overhead may not be worth it

## Future Enhancement Checklist

If we decide to add ghost-cursor:

- [ ] Install ghost-cursor in Docker image (done in Dockerfile.test)
- [ ] Create ghost_cursor_bridge.js script
- [ ] Implement GhostCursorIntegration Python class
- [ ] Update connection_extractor.py to use ghost cursor
- [ ] Test movement patterns on bot detection sites
- [ ] Compare warning rates with/without ghost-cursor
- [ ] Document performance impact
- [ ] Update TESTING_GUIDE.md with new tests

## Alternative: Pure Python Ghost Cursor

If we want better curves without Node.js dependency:

```python
# Using scipy for perfect Bezier curves

from scipy.interpolate import BSpline
import numpy as np

def bezier_curve(start, end, control_points, steps=50):
    """Generate Bezier curve points."""
    points = [start] + control_points + [end]
    t = np.linspace(0, 1, steps)

    # Calculate Bezier curve
    curve_points = []
    for ti in t:
        point = np.zeros(2)
        n = len(points) - 1
        for i, p in enumerate(points):
            # Bernstein polynomial
            b = (np.math.factorial(n) /
                 (np.math.factorial(i) * np.math.factorial(n - i))) * \
                (ti ** i) * ((1 - ti) ** (n - i))
            point += b * np.array(p)
        curve_points.append(point)

    return curve_points

# Usage
async def move_with_perfect_bezier(page, start, end):
    """Move mouse along perfect Bezier curve."""
    # Generate control points for natural curve
    control1 = (
        start[0] + random.uniform(-50, 50),
        start[1] + random.uniform(-50, 50)
    )
    control2 = (
        end[0] + random.uniform(-50, 50),
        end[1] + random.uniform(-50, 50)
    )

    curve = bezier_curve(start, end, [control1, control2])

    for point in curve:
        await page.mouse.move(point[0], point[1])
        await asyncio.sleep(0.01)  # 10ms per step
```

## Resources

- [ghost-cursor GitHub](https://github.com/Xetera/ghost-cursor)
- [ghost-cursor npm](https://www.npmjs.com/package/ghost-cursor)
- [Bezier Curves Explanation](https://javascript.info/bezier-curve)
- [Human Mouse Movement Patterns](https://link.springer.com/article/10.1007/s10207-017-0369-x)

---

**Status:** Optional enhancement - not required for MVP. Test current implementation first, then decide based on real data.
