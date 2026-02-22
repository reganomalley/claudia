# State Management Patterns

## The State Management Hierarchy

Before reaching for a state management library, work through this hierarchy top to bottom. Most apps need far less state management than developers think.

```
1. URL State (search params, route segments)
   └── Free, shareable, bookmarkable. Use it for filters, pagination, tabs, modals.
2. Local Component State (useState, ref, $state)
   └── Default for anything that belongs to one component.
3. Lifted State (props down, events up)
   └── When a parent and its children share state. Boring and correct.
4. Shared Context / Stores (Context, provide/inject, Svelte stores)
   └── When distant components need the same state and prop drilling is painful.
5. External State Management (Zustand, Pinia, Redux Toolkit)
   └── When you have complex shared state with significant logic.
6. Server State Cache (TanStack Query, SWR)
   └── This isn't state management -- it's caching. Most "state" is actually server data.
```

**The key insight:** Most applications that reach for Redux or Zustand on day one would be better served by URL state + local state + a server cache. The majority of "state management" problems are actually "I'm not caching my API responses properly" problems.

---

## React State Management

### useState / useReducer

**Use for:** Local component state. This is your default.

```
useState: simple values (toggles, form inputs, counts)
useReducer: state with multiple sub-values or complex update logic
```

**When to move beyond:** When you find yourself passing the same state through 3+ levels of components, or when multiple distant components need the same state.

### React Context

**Use for:** Avoiding prop drilling for relatively stable data (theme, locale, auth user, feature flags).

**Do NOT use for:** Frequently changing data. Every context update re-renders every consumer. A chat message count updating every second will re-render your entire app if it's in context.

**Pattern:** Keep contexts small and focused. One context for theme, another for auth, another for feature flags. Not one giant `AppContext` with everything.

### Zustand

**Use for:** Shared state that changes frequently, state with complex update logic, when you've outgrown Context.

**Why Zustand over Redux:** Less boilerplate, no providers needed, simpler mental model, good TypeScript support, tiny bundle (~1KB). It's the right default when you actually need a state library.

**When to use Redux Toolkit instead:** Large teams that benefit from Redux's enforced patterns, apps that need Redux DevTools' time-travel debugging, or when the team already knows Redux.

### Jotai / Recoil (Atomic State)

**Use for:** Fine-grained reactive state where individual atoms can update independently. Good for complex UIs where different parts of state update at different rates.

**Trade-off:** More atoms = more things to name and track. Can become hard to follow data flow in large apps.

---

## Vue State Management

### ref / reactive (Composition API)

**Use for:** All local component state. Vue's reactivity system is built into the framework -- you don't need a library for basic state.

```
ref: primitive values (strings, numbers, booleans)
reactive: objects and arrays
computed: derived state
watch/watchEffect: side effects on state changes
```

### provide / inject

**Use for:** Same as React Context -- avoiding prop drilling for stable data. Vue's version is simpler and more intuitive.

### Pinia

**Use for:** Shared state across components, complex state logic, anything that needs to survive component unmounting.

**Skip Vuex entirely.** Pinia is the official Vue state management library now. It's simpler, has better TypeScript support, and the Vue team recommends it. If you see a tutorial using Vuex, it's outdated.

**Pinia patterns:**
- One store per domain (useUserStore, useCartStore, useNotificationStore)
- Use getters for derived state
- Actions can be async
- Stores can reference other stores

---

## Svelte State Management

### Built-in Stores

Svelte's store system is usually all you need. It's built into the language.

```
writable: read + write from anywhere
readable: read-only (set internally, often from external sources)
derived: computed from other stores
```

**The `$` prefix auto-subscribes in components.** This is Svelte's killer feature for state management -- no boilerplate, no providers, no hooks.

### Svelte 5 Runes

Runes (`$state`, `$derived`, `$effect`) replace stores for component-level reactivity. For shared state, you can still use stores or create shared rune-based state with exported `$state`.

**When you might need more:** Almost never. If your Svelte app needs Redux-level state management, reconsider whether the state should live on the server instead.

---

## Server State: The Caching Pattern

### The Core Insight

Most "state management" complexity comes from treating server data as client state. When you fetch a list of users and put it in Redux, you're now responsible for:
- Loading states
- Error states
- Caching and invalidation
- Refetching when stale
- Optimistic updates
- Deduplication of requests

TanStack Query (React Query) and SWR solve all of this. They're not state management libraries -- they're server state caches.

### TanStack Query (React, Vue, Svelte, Solid)

**Use for:** Any data that comes from an API. This is your default for server data.

**Key concepts:**
- **Query keys** identify cached data (like cache keys)
- **Stale time** controls when data is considered stale
- **Refetch on window focus** keeps data fresh without polling
- **Mutations** handle writes with automatic cache invalidation
- **Optimistic updates** for responsive UI during mutations

**When to skip it:** If you're using a meta-framework with built-in data fetching (Next.js Server Components, Nuxt `useFetch`, SvelteKit `load`), start with that. Add TanStack Query when you need client-side caching beyond what the framework provides.

### SWR

Similar to TanStack Query but simpler API, React-only. Good for simpler use cases. TanStack Query is more feature-complete.

---

## Form State

### Controlled vs Uncontrolled

**Uncontrolled (use `ref` / `FormData`):** Simpler, less re-renders, good for simple forms. Let the DOM hold the state.

**Controlled (state per field):** Needed when you need to react to input changes in real-time (conditional fields, live validation, formatting).

**Default to uncontrolled.** Most forms don't need controlled inputs.

### Form Libraries

**React Hook Form:** Best React form library. Uncontrolled by default (performant), great validation with Zod/Yup integration, minimal re-renders.

**Formik:** Older, controlled by default (more re-renders), still widely used but React Hook Form is the better choice for new projects.

**Vue:** VeeValidate with Zod, or just use native Vue reactivity -- Vue's two-way binding makes forms easier than React.

**Svelte:** Native bindings (`bind:value`) handle most cases. No library needed for simple forms.

---

## Common Mistakes

### Putting Everything in Global State

**Problem:** Treating your state management library as a dumping ground. Theme, user, cart, form data, UI toggles, API responses -- all in one global store.

**Fix:** Only globalize state that is genuinely global. Most state is local. API data belongs in a cache (TanStack Query), not a store.

### Not Using URL State

**Problem:** Storing filters, pagination, active tabs, and modal state in component state or global store. User can't share links, back button doesn't work.

**Fix:** If the user would expect the back button to undo it, or would want to share a link to it, it belongs in the URL.

### Over-Fetching / Re-Fetching

**Problem:** Fetching the same data in multiple components, or refetching data that hasn't changed.

**Fix:** Use a server state cache (TanStack Query, SWR). It deduplicates requests and caches responses automatically.

### Premature State Management

**Problem:** Adding Redux/Zustand to a project on day one before you know what state you have.

**Fix:** Start with local state and URL state. Add a state library only when you have a concrete problem that local state can't solve. Most apps never reach that point.
