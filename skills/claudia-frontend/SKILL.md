---
name: claudia-frontend
description: >
  Frontend architecture knowledge domain for Claudia. Use this skill when the user asks about frontend
  frameworks, React vs Vue vs Svelte, state management, SSR vs SPA vs SSG, component patterns,
  CSS architecture, bundlers, or frontend infrastructure. Triggers on phrases like "which framework",
  "React or Vue", "state management", "SSR vs SPA", "Next.js vs", "Tailwind vs", "component library",
  "bundle size", "hydration", "islands architecture", or "frontend for".
version: 0.1.0
---

# Claudia Frontend Architecture Domain

## Overview

Frontend architecture is the art of choosing the right trade-off between developer experience, user experience, and complexity -- and then having the discipline to not add more tools until you've hit a real wall. Most frontend problems come from picking a stack that's too complex for what you're building, not from picking the "wrong" framework.

## Rendering Strategy Decision Tree

```
What are you building?
├── Content site (blog, docs, marketing)
│   └── SSG (Astro, Next.js static export, Hugo)
├── Interactive app (dashboard, SaaS, tool)
│   └── SPA (Vite + React/Vue/Svelte, or meta-framework with client rendering)
├── Both content AND interactive features
│   └── SSR / hybrid (Next.js, Nuxt, SvelteKit, Remix)
├── Content site with sprinkles of interactivity
│   └── Islands architecture (Astro, Eleventy + partial hydration)
└── Not sure
    └── Start with a meta-framework (Next.js or SvelteKit) -- they support all modes
```

## Framework Selection

| Framework | Sweet Spot | Honest Take |
|-----------|-----------|-------------|
| **React** | Biggest ecosystem, most jobs, most libraries | Verbose, needs the most decisions (state, routing, etc.), but you'll never lack for answers or hires |
| **Vue** | Best DX for small-to-medium apps, gentle learning curve | Template syntax is more approachable, Composition API is genuinely good, smaller ecosystem than React |
| **Svelte** | Least boilerplate, smallest bundles, best performance defaults | Smaller ecosystem, fewer jobs, but if you're building for yourself or a small team it's a joy |
| **Solid** | React-like API but truly reactive (no virtual DOM) | Tiny ecosystem, but signals-based reactivity is where the industry is heading |
| **Angular** | Enterprise, batteries-included, opinionated structure | Steep learning curve, heavy, but if your team needs guardrails and consistency at scale it delivers |

**The honest answer:** If you're building a career, learn React. If you're building a product and want speed, use Svelte or Vue. If you're in an enterprise, Angular might already be decided for you.

## Meta-Framework Comparison

| Framework | Built On | Best At | Watch Out For |
|-----------|---------|---------|---------------|
| **Next.js** | React | Full-stack React apps, Vercel deployment, huge ecosystem | App Router complexity, vendor lock-in pressure, heavy for simple sites |
| **Nuxt** | Vue | Vue full-stack apps, auto-imports, convention over config | Smaller community than Next, some modules lag behind |
| **SvelteKit** | Svelte | Small-to-medium full-stack apps, elegant API, fast | Smaller ecosystem, fewer deployment adapters |
| **Astro** | Any (islands) | Content sites with optional interactivity, multi-framework support | Not ideal for highly interactive apps, newer ecosystem |
| **Remix** | React | Data loading patterns, progressive enhancement, web standards | Merged into React Router v7, uncertain future trajectory |

## State Management Decision Tree

```
Where should this state live?
├── URL (search params, route segments)
│   └── Use it. Shareable, bookmarkable, free.
├── Single component
│   └── Local state (useState, ref, $state)
├── Parent + a few children
│   └── Props down, events up (the boring right answer)
├── Distant components need it
│   └── Context / stores (React Context, Vue provide/inject, Svelte stores)
├── Complex shared state with logic
│   └── External store (Zustand, Pinia, Redux Toolkit)
└── Server data (API responses, database state)
    └── NOT state management -- use a cache (TanStack Query, SWR, Nuxt useFetch)
```

## Quick Comparisons

| Decision | Default Choice | When to Switch |
|----------|---------------|----------------|
| Framework | React | Want better DX and smaller bundles? Svelte. Need Vue's template syntax? Vue. |
| Meta-framework | Next.js | Content-heavy? Astro. Vue-based? Nuxt. Want simplicity? SvelteKit. |
| Styling | Tailwind | Need runtime dynamic styles? CSS Modules + custom properties. Building a component lib? vanilla-extract. |
| State management | Local state + URL | Need shared state? Zustand (React), Pinia (Vue), stores (Svelte). |
| Server state | TanStack Query | Using a meta-framework? Use its built-in data fetching. |
| Bundler | Vite | Using Next.js? Turbopack. Publishing a library? Rollup or tsup. |
| Forms | React Hook Form / native | Simple forms? Don't use a library. Complex validation? Zod + form library. |

## Deep References

For detailed guidance on specific topics, load:
- `references/frameworks-rendering.md` -- Deep framework comparison and rendering strategies
- `references/state-management.md` -- State management patterns per framework
- `references/css-bundling.md` -- CSS approaches, bundlers, and performance

## Response Format

When advising on frontend architecture:
1. **Recommendation** (specific framework/tool/pattern)
2. **Why it fits** (match to their use case, team, and constraints)
3. **What you're trading off** (what this choice is worse at)
4. **Start with** (the concrete first step -- a command, a template, a file structure)
