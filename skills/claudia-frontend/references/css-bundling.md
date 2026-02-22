# CSS Approaches & Bundling

## CSS Architecture

### Tailwind CSS (Utility-First)

**How it works:** Utility classes applied directly in markup. No separate CSS files, no naming conventions, no cascade issues.

**Pros:**
- Fastest iteration speed -- style without leaving your template
- Design constraints built in (spacing scale, color palette, breakpoints)
- Purged output is tiny (only classes you use ship to production)
- Co-located styles -- you see what a component looks like by reading its markup
- Consistent design system out of the box

**Cons:**
- Markup gets cluttered with classes (mitigated by components/`@apply`)
- Learning curve for the utility names
- Harder to do truly custom/unusual designs (you can, but you fight the system)
- Dynamic styles require `class:` bindings or `style` attributes

**Use when:** Rapid iteration, design-system-driven projects, teams that want consistency without writing CSS. This is the default choice for most new projects.

### CSS Modules

**How it works:** CSS files with locally scoped class names. Write normal CSS, import it, get unique class names at build time.

**Pros:**
- Scoped by default -- no naming collisions
- It's just CSS -- no new syntax to learn
- Works great with SSR (no runtime)
- Good TypeScript integration with typed-css-modules

**Cons:**
- Still need a naming convention within each module
- Composition between modules requires `composes` keyword
- No design system constraints built in
- Separate file per component

**Use when:** Teams with strong CSS knowledge, SSR-heavy apps, when you want scoping without a paradigm shift.

### CSS-in-JS (styled-components, Emotion)

**How it works:** Write CSS in JavaScript template literals or objects. Styles are generated at runtime and injected into the page.

**Pros:**
- Full JavaScript power for dynamic styles
- Component-scoped by default
- Good for component libraries (styles ship with the component)
- Theming is natural (JavaScript objects)

**Cons:**
- Runtime cost: styles are computed and injected on every render
- Larger bundle size (the library + your styles in JS)
- SSR requires extra setup to avoid flash of unstyled content
- React Server Components don't support runtime CSS-in-JS

**The runtime cost reality:** For most apps, the runtime overhead is negligible. It starts to matter for high-performance apps with frequent re-renders, long lists, or animations. If you're not measuring a problem, you don't have one.

**Use when:** Building a component library, need heavily dynamic styles, small-to-medium apps where runtime cost doesn't matter.

### Zero-Runtime CSS-in-JS (vanilla-extract, Linaria, Panda CSS)

**How it works:** Write styles in TypeScript, extracted to static CSS at build time. You get the DX of CSS-in-JS without the runtime cost.

**Pros:**
- Type-safe styles with full TypeScript support
- No runtime cost (compiled to static CSS)
- Works with SSR and React Server Components
- Sprinkles API (vanilla-extract) gives you type-safe utility classes

**Cons:**
- Build step required
- Less dynamic than runtime CSS-in-JS
- Smaller community than Tailwind or styled-components

**Use when:** Building design systems, component libraries, or apps where type-safe styles and zero runtime cost both matter.

### Vanilla CSS (Custom Properties + BEM)

**How it works:** Plain CSS with custom properties (variables) for theming and BEM naming convention for scoping.

**Pros:**
- No build tool dependency
- Browser-native, zero runtime cost
- Custom properties cascade naturally (great for theming)
- Everyone knows CSS

**Cons:**
- No built-in scoping (BEM is a convention, not enforced)
- No design system constraints
- Verbose naming
- Global namespace issues at scale

**Use when:** Small projects, server-rendered apps with minimal JS, when you want zero dependencies.

---

## CSS Decision Table

| Situation | Recommendation | Why |
|-----------|---------------|-----|
| New project, general purpose | Tailwind | Fastest iteration, good defaults, tiny output |
| Existing project with CSS knowledge | CSS Modules | Scoped without a paradigm shift |
| Component library for distribution | vanilla-extract or CSS Modules | No runtime dep for consumers |
| Dynamic theme-heavy app | CSS custom properties + Tailwind | CSS variables handle theming, Tailwind handles the rest |
| Need runtime dynamic styles | styled-components or Emotion | Full JS power, but accept the runtime cost |
| SSR-first, minimal JS | CSS Modules or vanilla CSS | No runtime, no flash of unstyled content |

---

## Bundlers

### Vite

**The default choice.** Fast dev server (native ES modules, no bundling in dev), Rollup-based production builds, excellent plugin ecosystem.

**Use for:** Everything, unless you have a specific reason not to. React, Vue, Svelte, Solid, vanilla -- Vite supports all of them.

**Why it's fast:** Dev server serves files as native ES modules. The browser does the module resolution. Only the file you changed is re-processed. No full bundle on every save.

### Webpack

**Legacy, but still everywhere.** Complex configuration, slow dev server (full bundle), but massive plugin ecosystem and handles every edge case.

**Use for:** Existing projects that already use it. Don't start new projects with webpack unless you need a specific webpack plugin that doesn't exist for Vite.

### Turbopack

**Next.js's bundler.** Written in Rust, designed as webpack's successor within the Next.js ecosystem.

**Use for:** Next.js projects (it's the default in Next.js 15+). Not available outside Next.js.

### esbuild

**Extremely fast (written in Go).** Minimal plugin API, no code splitting in the way webpack/Rollup do it.

**Use for:** Library builds, TypeScript transpilation, simple build scripts. Not a full app bundler.

### Rollup

**Clean output, excellent tree shaking.** The engine behind Vite's production builds.

**Use for:** Publishing libraries to npm. Rollup produces the cleanest, smallest output for library code. For apps, use Vite (which uses Rollup under the hood).

### tsup

**Zero-config library bundler.** Built on esbuild. Handles TypeScript, generates CJS + ESM + type declarations.

**Use for:** Publishing TypeScript libraries to npm. Simpler than Rollup for library builds.

### Bundler Decision

| Building | Use | Why |
|----------|-----|-----|
| Web app (any framework) | Vite | Fast dev, good production builds, great DX |
| Next.js app | Turbopack (built in) | It's the default, optimized for Next.js |
| npm library | tsup or Rollup | Clean output, CJS + ESM, type declarations |
| Simple build script | esbuild | Fastest, minimal config |
| Legacy app | webpack (already there) | Don't migrate for the sake of migrating |

---

## Bundle Optimization

### Code Splitting

**What:** Breaking your bundle into smaller chunks that load on demand.

**How:** Dynamic `import()` creates a split point. The bundler creates a separate chunk for the imported module.

**Where to split:**
- Routes (each page is a chunk -- meta-frameworks do this automatically)
- Heavy libraries (chart libraries, editors, PDF generators)
- Below-the-fold content (modals, tabs, accordions)
- Feature flags (don't load code for features the user doesn't have)

### Tree Shaking

**What:** Eliminating unused code from the final bundle.

**Requirements:** ES modules (`import`/`export`), not CommonJS (`require`). Side-effect-free modules. Mark packages as `"sideEffects": false` in `package.json`.

**Common gotcha:** Barrel files (`index.ts` that re-exports everything) can break tree shaking. If you import one function from a barrel file, some bundlers include everything.

### Lazy Loading

**Components:** `React.lazy()`, Vue's `defineAsyncComponent`, Svelte's `{#await import(...)}`.

**Images:** Native `loading="lazy"` attribute. Use it on every image below the fold.

**Routes:** Meta-frameworks handle this automatically. For SPAs, lazy-load route components.

### Dynamic Imports

```
// Instead of:
import { heavyFunction } from './heavy-module'

// Do:
const { heavyFunction } = await import('./heavy-module')
```

Only load code when the user actually needs it. A PDF export feature that 5% of users click should not be in the initial bundle.

---

## Font Loading

**Best practice:** Self-host fonts. Google Fonts adds a render-blocking request to a third-party server.

**Strategy:**
1. Subset your fonts (only include characters you use)
2. Use `font-display: swap` (show fallback immediately, swap when loaded)
3. Preload the most important font: `<link rel="preload" as="font" crossorigin>`
4. Use variable fonts when available (one file for all weights)
5. WOFF2 format only (best compression, universal support)

**Size budget:** A single font file should be under 50KB after subsetting. If you're shipping 500KB of fonts, you have too many weights or aren't subsetting.

## Image Optimization

**Formats:**
- AVIF: Best compression, good support (use as primary)
- WebP: Good compression, universal support (use as fallback)
- PNG: Lossless, use only when transparency is needed and AVIF/WebP aren't suitable
- SVG: Icons and illustrations (not photos)

**Responsive images:** Use `srcset` and `sizes` attributes. Serve appropriately sized images -- don't send a 4000px image to a 375px phone screen.

**Meta-framework image components:** `next/image`, `nuxt-image`, `@astrojs/image` -- these handle optimization, responsive sizing, lazy loading, and format conversion automatically. Use them.

## Core Web Vitals

| Metric | What It Measures | Target | Common Fix |
|--------|-----------------|--------|------------|
| LCP (Largest Contentful Paint) | When the biggest element renders | < 2.5s | Optimize hero image, preload fonts, SSR/SSG |
| INP (Interaction to Next Paint) | Responsiveness to user input | < 200ms | Break up long tasks, reduce main thread work, defer non-critical JS |
| CLS (Cumulative Layout Shift) | Visual stability | < 0.1 | Set explicit image dimensions, reserve space for dynamic content, avoid injecting content above the fold |

**The fastest site is the one that sends the least JavaScript.** Every KB of JS must be downloaded, parsed, compiled, and executed. HTML and CSS are faster to process. Default to sending less JS and add more only when you need interactivity.
