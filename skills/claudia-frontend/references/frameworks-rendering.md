# Frameworks & Rendering Strategies

## Framework Deep Dive

### React

**Honest pros:**
- Largest ecosystem by far -- a library exists for everything
- Most jobs, most tutorials, most StackOverflow answers
- Composition model is genuinely powerful (hooks, custom hooks)
- React Server Components are a real innovation for data-heavy apps
- React Native lets you share logic with mobile

**Honest cons:**
- Verbose. A simple component is more code than Vue or Svelte equivalents
- You make every decision: state, routing, styling, project structure
- `useEffect` is a footgun (dependency arrays, cleanup, double-firing in strict mode)
- The ecosystem moves fast and fragments (class components, hooks, server components, use() -- four eras in 8 years)
- Bundle size floor is higher than Svelte/Solid because of the virtual DOM runtime

**Use when:** You need the ecosystem, you're hiring React developers, or you're already in React.

### Vue

**Honest pros:**
- Best developer experience for small-to-medium apps
- Template syntax is approachable for people coming from HTML/CSS
- Composition API (Vue 3) is as powerful as React hooks but cleaner
- Single-file components (SFC) are genuinely nice -- template, script, style in one file
- Pinia is an excellent built-in-ish state management story

**Honest cons:**
- Smaller ecosystem than React -- some niche libraries don't have Vue versions
- Fewer jobs (depending on market)
- Options API vs Composition API split confuses newcomers
- TypeScript support is good now but was bolted on later

**Use when:** You want productive DX without React's decision fatigue, especially for internal tools, dashboards, or small-medium products.

### Svelte

**Honest pros:**
- Least boilerplate of any framework -- reactivity is built into the language
- Smallest bundle sizes (compiles away the framework)
- Best performance defaults (no virtual DOM overhead)
- SvelteKit is elegant and well-designed
- Runes (Svelte 5) bring explicit reactivity without losing simplicity

**Honest cons:**
- Smallest ecosystem of the big three
- Fewer jobs and fewer developers who know it
- Some edge cases in reactivity can be surprising
- Svelte 5 (runes) is a significant API shift from Svelte 4

**Use when:** You're building for yourself or a small team, you care about performance, or you want to ship fast without fighting your framework.

### Solid

**Honest pros:**
- React-like API but with true reactivity (signals, not virtual DOM diffing)
- Extremely fast -- consistently tops benchmarks
- Fine-grained reactivity means no unnecessary re-renders
- JSX without the React baggage

**Honest cons:**
- Tiny ecosystem -- you'll build things yourself or go without
- Few jobs asking for Solid specifically
- Destructuring props breaks reactivity (a common gotcha)
- SolidStart (meta-framework) is still maturing

**Use when:** You love React's mental model but want real reactivity and peak performance, and you're comfortable with a smaller ecosystem.

### Angular

**Honest pros:**
- Batteries included: routing, forms, HTTP client, testing, i18n -- all built in
- Opinionated structure means consistency across teams
- Excellent TypeScript integration (it's TypeScript-first)
- Dependency injection is powerful for large apps
- Signals arriving in Angular 17+ modernize the reactivity model

**Honest cons:**
- Steep learning curve (decorators, modules, DI, RxJS, zones)
- Heavy -- both in bundle size and conceptual overhead
- Verbose -- even simple things require ceremony
- RxJS is powerful but complex for newcomers

**Use when:** Enterprise, large teams that need enforced structure, or when the organization has already chosen Angular.

---

## Rendering Strategies Explained

### Client-Side Rendering (CSR / SPA)

**How it works:** Server sends a near-empty HTML shell. JavaScript downloads, executes, and renders the page in the browser.

**Pros:** Simple deployment (static files), good for highly interactive apps, fast subsequent navigations.
**Cons:** Slow initial load (download + parse + execute JS), poor SEO without extra work, blank screen until JS loads.

**Use for:** Dashboards, admin panels, internal tools, apps behind login -- anything where SEO doesn't matter and interactivity is primary.

### Server-Side Rendering (SSR)

**How it works:** Server renders HTML for each request. Browser receives full HTML, then "hydrates" it (attaches JavaScript event handlers).

**Pros:** Fast first paint (HTML arrives ready), good SEO, works without JavaScript (progressively enhanced).
**Cons:** Server cost per request, hydration cost (downloading and running JS to make the page interactive), TTFB depends on server speed.

**Use for:** E-commerce, content sites that also need interactivity, SEO-critical pages with dynamic data.

### Static Site Generation (SSG)

**How it works:** Pages are rendered to HTML at build time. The result is static files served from a CDN.

**Pros:** Fastest possible delivery (CDN-cached HTML), cheapest to host, excellent SEO, most secure (no server to attack).
**Cons:** Build time grows with page count, content is stale until rebuild, not suitable for personalized or real-time content.

**Use for:** Blogs, documentation, marketing sites, landing pages -- anything where content changes infrequently.

### Incremental Static Regeneration (ISR)

**How it works:** Static pages that regenerate in the background after a configurable time period. First request after expiry serves stale content while regenerating.

**Pros:** Static performance with fresher content, no full rebuild for updates.
**Cons:** Next.js-specific (mostly), stale content during revalidation window, complex caching behavior.

**Use for:** E-commerce product pages, blogs with frequent updates, content that changes hourly/daily but not per-request.

### Streaming SSR

**How it works:** Server sends HTML in chunks as components resolve. The browser renders progressively -- header first, then content, then sidebar.

**Pros:** Perceived performance is excellent (user sees content immediately), Suspense boundaries let you stream in stages.
**Cons:** More complex implementation, not all hosting supports streaming, debugging is harder.

**Use for:** Pages with mixed fast/slow data sources -- show the fast parts immediately, stream in the slow parts.

### Islands Architecture

**How it works:** The page is static HTML by default. Only specific "islands" of interactivity are hydrated with JavaScript. The rest stays as zero-JS HTML.

**Pros:** Minimal JavaScript sent to the browser, excellent performance, progressive enhancement by default.
**Cons:** Islands are isolated (sharing state between them requires extra work), newer pattern with fewer battle-tested examples.

**Use for:** Content sites with sprinkles of interactivity (a search widget, a newsletter form, an interactive chart on an otherwise static page).

---

## Meta-Framework Deep Dive

### Next.js (React)

**App Router vs Pages Router:**
- Pages Router: Simpler, file-based routing, `getServerSideProps`/`getStaticProps`. Well-understood, lots of examples.
- App Router: React Server Components, nested layouts, streaming, server actions. More powerful but significantly more complex.
- **Recommendation:** New projects should use App Router, but be prepared for a steeper learning curve. If you need to ship fast and the team is new to Next.js, Pages Router is still fine.

**The Vercel question:** Next.js works great on Vercel. It also works elsewhere (Docker, AWS, self-hosted), but some features (ISR, image optimization, middleware at the edge) work best or only on Vercel. Know what you're signing up for.

### Nuxt 3 (Vue)

- Server routes, auto-imports, convention-based structure
- `useFetch` and `useAsyncData` handle server/client data fetching elegantly
- Nitro server engine is genuinely good (deploys to many targets)
- Smaller community than Next.js but the DX is arguably better

### SvelteKit (Svelte)

- The most elegant API of any meta-framework
- Load functions for data, form actions for mutations -- clean separation
- Adapter system for deployment targets (Node, Vercel, Cloudflare, static)
- Smaller ecosystem but growing

### Astro

- Content-first framework -- renders to zero-JS HTML by default
- Use any UI framework for interactive islands (React, Vue, Svelte, Solid)
- Content Collections for type-safe markdown/MDX
- Not designed for highly interactive apps -- use it for what it's good at

---

## The "Just Use Next.js" Rule

Next.js is the PostgreSQL of frontend: it handles 80% of use cases well. Before reaching for something else, ask:
- Is my team already in the React ecosystem?
- Do I need SSR, SSG, and API routes in one framework?
- Do I want the largest community and most examples?

If yes to all three, Next.js is the safe choice.

**Break the rule when:**
- You're building a pure content site (Astro will be faster and simpler)
- You prefer Vue or Svelte's DX and your team agrees
- You need the smallest possible bundle (Svelte/Solid)
- You're building a simple SPA and don't need SSR (Vite + your framework)
- You want to avoid Vercel lock-in and you're using features that tie you to their platform

## Performance Implications

| Strategy | JS Sent to Client | Time to First Byte | Time to Interactive | SEO |
|----------|-------------------|--------------------|--------------------|-----|
| CSR (SPA) | High | Fast (empty shell) | Slow (must download + execute all JS) | Poor (without SSR/prerendering) |
| SSR | Medium-High (hydration) | Slower (server renders) | Medium (hydration cost) | Good |
| SSG | Low-Medium | Fastest (CDN) | Fast | Excellent |
| ISR | Low-Medium | Fast (cached) | Fast | Excellent |
| Streaming SSR | Medium-High | Fast (first chunk) | Progressive | Good |
| Islands | Very Low | Fast (mostly static) | Fast (only islands hydrate) | Excellent |

The performance gap between these strategies matters less on fast connections and modern devices. It matters a lot on slow 3G connections and budget phones. Know your users.
