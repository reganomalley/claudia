# Frontend Performance

## Core Web Vitals

Google's metrics for real-user experience. These affect search ranking and, more importantly, whether users stick around.

### LCP (Largest Contentful Paint)

**What it measures:** Time until the largest visible element (image, heading, text block) renders.

**Targets:** Good < 2.5s. Needs improvement 2.5-4s. Poor > 4s.

**Common causes of bad LCP:**
- Slow server response (high TTFB)
- Render-blocking CSS/JS
- Large unoptimized hero image
- Web fonts blocking text render
- Client-side rendering with no SSR

**Fixes:**
- Reduce TTFB: CDN, edge rendering, server caching
- Preload the LCP image: `<link rel="preload" as="image" href="hero.webp">`
- Inline critical CSS, defer the rest
- Use `font-display: swap` so text renders immediately
- SSR or SSG for above-the-fold content

### INP (Interaction to Next Paint)

**What it measures:** Responsiveness. Latency from user interaction (click, tap, keypress) to the next visual update. Replaced FID in March 2024.

**Targets:** Good < 200ms. Needs improvement 200-500ms. Poor > 500ms.

**Common causes of bad INP:**
- Long JavaScript tasks blocking the main thread
- Heavy event handlers (re-rendering large component trees)
- Layout thrashing in response to input
- Third-party scripts hogging the main thread

**Fixes:**
- Break up long tasks with `setTimeout(fn, 0)` or `scheduler.yield()`
- Debounce/throttle input handlers
- Use `startTransition` in React for non-urgent updates
- Virtualize long lists (react-window, tanstack-virtual)
- Audit third-party scripts -- remove or defer what you can

### CLS (Cumulative Layout Shift)

**What it measures:** Visual stability. How much the page layout shifts unexpectedly during loading.

**Targets:** Good < 0.1. Needs improvement 0.1-0.25. Poor > 0.25.

**Common causes of bad CLS:**
- Images without dimensions
- Ads or embeds injected without reserved space
- Web fonts causing text reflow
- Dynamic content inserted above existing content

**Fixes:**
- Always set `width` and `height` on images (or use `aspect-ratio` CSS)
- Reserve space for ads/embeds with fixed-size containers
- Use `font-display: swap` + `size-adjust` for font metrics matching
- Don't insert content above the viewport after initial render

## Bundle Optimization

### Code Splitting

Don't ship code users don't need yet.

```javascript
// Route-based splitting (React)
const Dashboard = React.lazy(() => import('./Dashboard'));
const Settings = React.lazy(() => import('./Settings'));

// Next.js does this automatically for pages/app routes

// Feature-based splitting
const HeavyChart = React.lazy(() => import('./HeavyChart'));
// Only loads when the chart is actually rendered
```

### Tree Shaking

Import only what you use. Bundlers eliminate dead code, but only if you let them.

```javascript
// Bad: imports entire library (lodash is 70KB+ minified)
import _ from 'lodash';
_.get(obj, 'path');

// Good: import specific function (4KB)
import get from 'lodash/get';

// Better: use lodash-es for full tree shaking
import { get } from 'lodash-es';

// Best: write it yourself (it's one line)
const get = (obj, path) => path.split('.').reduce((o, k) => o?.[k], obj);
```

### Analyzing Your Bundle

You can't optimize what you can't see.

```bash
# Webpack
npx webpack-bundle-analyzer stats.json

# Vite
npm install -D rollup-plugin-visualizer
# Add to vite.config.js: import { visualizer } from 'rollup-plugin-visualizer'

# Next.js
ANALYZE=true next build  # with @next/bundle-analyzer

# Quick check: what's actually big?
npx source-map-explorer dist/assets/*.js
```

**What to look for:**
- Dependencies larger than your app code (moment.js, lodash full build)
- Duplicate dependencies (two versions of the same library)
- Polyfills you don't need (check your browser targets)
- Dev-only code leaking into production

## Image Optimization

Images are usually the heaviest assets on a page. Fix images first.

**Format selection:**
- **AVIF**: Best compression, growing support. Use with `<picture>` fallback.
- **WebP**: Good compression, broad support. Default choice.
- **PNG**: Only for images needing transparency + lossless (logos, icons).
- **JPEG**: Legacy. Use WebP/AVIF instead.
- **SVG**: Icons and simple graphics. Inline for small ones, sprite for many.

**Responsive images:**
```html
<picture>
  <source srcset="hero.avif" type="image/avif">
  <source srcset="hero.webp" type="image/webp">
  <img src="hero.jpg" alt="..." width="1200" height="600" loading="lazy">
</picture>

<!-- Responsive sizes -->
<img
  srcset="photo-400.webp 400w, photo-800.webp 800w, photo-1200.webp 1200w"
  sizes="(max-width: 600px) 400px, (max-width: 1000px) 800px, 1200px"
  src="photo-800.webp"
  alt="..."
  loading="lazy"
>
```

**CDN image transforms:** Use Cloudflare Images, imgix, or Vercel Image Optimization to resize/convert on the fly instead of generating every size at build time.

**Lazy loading:** `loading="lazy"` on every image below the fold. Do NOT lazy-load the LCP image (above the fold) -- that makes LCP worse.

## Font Loading

Web fonts cause invisible text (FOIT) or layout shifts (FOUT). Handle them properly.

```css
/* Use font-display: swap -- show fallback immediately, swap when loaded */
@font-face {
  font-family: 'MyFont';
  src: url('/fonts/myfont.woff2') format('woff2');
  font-display: swap;
}
```

**Best practices:**
- **Preload** your primary font: `<link rel="preload" href="/fonts/main.woff2" as="font" type="font/woff2" crossorigin>`
- **Subset** fonts to only the characters you use (latin, latin-ext). Tools: `glyphhanger`, `pyftsubset`.
- **Variable fonts**: One file replaces multiple weights/styles. Fewer requests, smaller total size.
- **Self-host** instead of Google Fonts. Eliminates third-party connection overhead and privacy concerns.
- **Fallback metrics matching**: Use `size-adjust`, `ascent-override`, `descent-override` to match fallback font metrics and reduce CLS.

## Rendering Performance

### Avoid Layout Thrashing

Reading layout properties (offsetHeight, getBoundingClientRect) forces the browser to recalculate layout. Alternating reads and writes in a loop is called "layout thrashing."

```javascript
// Bad: forces layout recalc on every iteration
elements.forEach(el => {
  const height = el.offsetHeight;    // read (forces layout)
  el.style.height = height + 10 + 'px'; // write (invalidates layout)
});

// Good: batch reads, then batch writes
const heights = elements.map(el => el.offsetHeight);  // all reads
elements.forEach((el, i) => {
  el.style.height = heights[i] + 10 + 'px';           // all writes
});

// Better: use requestAnimationFrame for writes
const heights = elements.map(el => el.offsetHeight);
requestAnimationFrame(() => {
  elements.forEach((el, i) => {
    el.style.height = heights[i] + 10 + 'px';
  });
});
```

### CSS Containment

Tell the browser what doesn't affect the rest of the page.

```css
/* content-visibility: auto -- browser skips rendering off-screen elements */
.card {
  content-visibility: auto;
  contain-intrinsic-size: 0 200px; /* estimated size for scroll */
}

/* contain: layout -- changes inside this element don't affect outside layout */
.widget {
  contain: layout style;
}
```

### Virtualization for Long Lists

Don't render 10,000 DOM nodes. Render the ~20 that are visible.

```javascript
// react-window (lightweight)
import { FixedSizeList } from 'react-window';
<FixedSizeList height={600} itemCount={10000} itemSize={50} width="100%">
  {({ index, style }) => <div style={style}>Row {index}</div>}
</FixedSizeList>

// @tanstack/react-virtual (more flexible, headless)
const virtualizer = useVirtualizer({
  count: 10000,
  getScrollElement: () => parentRef.current,
  estimateSize: () => 50,
});
```

## Network Optimization

- **HTTP/2**: Multiplexing means you don't need to bundle everything into one file. Most hosts support this. Verify with DevTools Network tab.
- **Preconnect**: Establish early connections to critical third-party origins.
  ```html
  <link rel="preconnect" href="https://api.example.com">
  <link rel="dns-prefetch" href="https://analytics.example.com">
  ```
- **Prefetch**: Load resources for likely next navigations.
  ```html
  <link rel="prefetch" href="/dashboard.js">  <!-- next page's bundle -->
  ```
- **Compression**: Brotli is 15-20% smaller than gzip. Most CDNs and servers support it. Verify with `Content-Encoding: br` in response headers.

## Lighthouse and Real-User Monitoring

**Lighthouse** (lab data): Good for development, catches obvious issues. Run in Chrome DevTools or CI. But lab data != real-user experience.

**Real-User Monitoring (RUM)**: Measures actual users on actual devices and networks. This is what matters.

- **web-vitals** library: Google's tiny library for measuring CWV in the browser.
  ```javascript
  import { onLCP, onINP, onCLS } from 'web-vitals';
  onLCP(metric => sendToAnalytics(metric));
  onINP(metric => sendToAnalytics(metric));
  onCLS(metric => sendToAnalytics(metric));
  ```
- **Services**: Vercel Analytics (built-in if on Vercel), SpeedCurve, Sentry Performance, Datadog RUM.
- **CrUX** (Chrome UX Report): Real Chrome user data for your origin. Free. Available in PageSpeed Insights and BigQuery.

Look at **p75** (75th percentile), not averages. Your median user might be fine while your p75 user on a slow phone in a bad network is suffering.

## React-Specific Performance

### React.memo

Prevents re-renders when props haven't changed. You almost never need this.

```javascript
// Only use when:
// 1. Component re-renders frequently with the same props
// 2. The render itself is expensive (confirmed by profiling)
// 3. You've confirmed it actually helps (measure before and after)
const ExpensiveList = React.memo(function ExpensiveList({ items }) {
  return items.map(item => <ComplexItem key={item.id} item={item} />);
});
```

**Why you usually don't need it:** React's reconciliation is already fast. The overhead of shallow-comparing props on every render is often more expensive than just re-rendering. Profile first.

### useMemo and useCallback

These are for **referential equality**, not performance. Use them when a child component or effect depends on a reference being stable.

```javascript
// Correct use: stabilize a reference for a dependency array
const filters = useMemo(() => ({ status, type }), [status, type]);
useEffect(() => { fetchData(filters); }, [filters]);

// Correct use: stabilize a callback passed to a memoized child
const handleClick = useCallback((id) => {
  setSelected(id);
}, []);

// Wrong use: "optimizing" a cheap computation
const doubled = useMemo(() => value * 2, [value]); // useMemo costs more than the multiplication
```

### React Compiler (React 19+)

The React Compiler automatically memoizes components and hooks. If you're on React 19+, it handles most of the cases where you'd manually use `React.memo`, `useMemo`, and `useCallback`.

**What it does:** Analyzes your components at build time and inserts memoization where it would actually help. Better than human judgment because it can track exact dependencies.

**What this means:** Stop sprinkling `useMemo` everywhere "just in case." Write straightforward code and let the compiler optimize. Manual memoization is still useful for genuinely expensive computations, but the compiler handles the referential equality cases.
