# UI Migration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Migrate Kimi-generated landing page components into the Next.js frontend app and set up routing for the marketing homepage.

**Architecture:** We will move the current chat interface from `src/app/page.tsx` to `src/app/chat/page.tsx`. We will copy Kimi's `App.tsx` structure to the new `src/app/page.tsx`. Corresponding Kimi components will be moved to `src/sections` and `src/components`. Tailwind config and global css will be merged.

**Tech Stack:** Next.js 15, TailwindCSS v4, Framer Motion, Lucide React

---
### Task 1: Relocate Chat Route
**Files:**
- Create: `frontend/src/app/chat/page.tsx`
- Modify: `frontend/src/app/page.tsx` 

**Step 1: Move existing chat page**
Move `frontend/src/app/page.tsx` to `frontend/src/app/chat/page.tsx`. This keeps the existing Chat application functional at a new route.

**Step 2: Commit**
```bash
cd frontend
git add src/app/chat/page.tsx src/app/page.tsx
git commit -m "refactor: move chat page to /chat route"
```

### Task 2: Copy Kimi Components and Assets
**Files:**
- Copy: `Kimi_Agent_欧美两性AI UI优化/app/src/sections/*` to `frontend/src/sections/*`
- Copy: `Kimi_Agent_欧美两性AI UI优化/app/src/components/*` to `frontend/src/components/*`
- Copy: `Kimi_Agent_欧美两性AI UI优化/app/public/images/*` to `frontend/public/images/*`

**Step 1: Copy directories**
Execute file copies to move sections, specialized components, and images.

**Step 2: Commit**
```bash
cd frontend
git add src/sections src/components public/images
git commit -m "feat: migrate ui components and assets from kimi prototype"
```

### Task 3: Establish Marketing Homepage
**Files:**
- Create/Modify: `frontend/src/app/page.tsx`

**Step 1: Write the new landing page**
Write the new `frontend/src/app/page.tsx` based on the structure of Kimi's `App.tsx`, integrating Navbar, Hero, FeaturesSection, etc. Update Links to point to `/chat`.

**Step 2: Commit**
```bash
cd frontend
git add src/app/page.tsx
git commit -m "feat: implement new marketing homepage structure"
```

### Task 4: Merge Styles and Configuration
**Files:**
- Modify: `frontend/src/app/globals.css`

**Step 1: Merge CSS**
Copy custom animations, keyframes, and tailored colors (e.g., cyber-black) from Kimi's `index.css` and `tailwind.config.ts` into `frontend/src/app/globals.css` (Tailwind v4 syntax using `@theme`).

**Step 2: Adjust CTA Links in sections**
Review all copied sections in `src/sections/` and update any "GET STARTED" or "START FREE TRIAL" buttons to link to `/chat` using Next.js `<Link>`.

**Step 3: Run Build to verify**
Run: `cd frontend && npm run build`
Expected: Next.js build completes with no lint or type errors.

**Step 4: Commit**
```bash
cd frontend
git add src/app/globals.css src/sections
git commit -m "feat: merge tailwind styles and fix routing links"
```
