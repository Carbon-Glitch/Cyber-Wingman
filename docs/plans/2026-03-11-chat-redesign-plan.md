# Chat Interface Redesign Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Redesign the `/chat` route using the UI/UX from the Kimi prototype (`code.html`), ensuring it matches the branding of the new landing page, and implement automatic routing/prompt selection based on the user's gender and relationship status (defaulting to Single Male / "Alpha 教官" for local testing).

**Architecture:** We will replace the current chat layout with the new cyberpunk-themed layout featuring a left sidebar and a stylized top header. We'll update the backend `ChatService` or frontend prompt selection logic to ensure the correct prompt is used based on the user's profile.

**Tech Stack:** Next.js 15, Tailwind CSS V4, React (Lucide React, Framer Motion), Python (FastAPI/LangChain for backend)

---

### Task 1: Scaffolding the New Chat UI Layout

**Files:**
- Modify: `d:\project\Cyber_Wingman\frontend\src\app\chat\page.tsx`

**Step 1: Replace the outer shell**
- Integrate the left sidebar (`<aside>`) from `code.html` into the existing layout.
- Integrate the top header (`<header>`) from `code.html`.
- Preserve the existing state management (sessions, messages, mode) but adapt the UI to fit inside the `<main>` container with the `grid-bg scanline-effect` styling.

**Step 2: Migrate Core Chat Components**
- Ensure `ReplyOptionsCard`, `CollapsibleThinkingPanel`, etc. fit within the new dark theme correctly.
- Implement the "Centerpiece Brand Area" when the chat is empty.

### Task 2: Implementing Automatic Persona Routing (Frontend State)

**Files:**
- Modify: `d:\project\Cyber_Wingman\frontend\src\app\chat\page.tsx`

**Step 1: Define User Profile State**
- Add state/context to mock the user profile (Gender: Male, Status: Single).
- Based on this profile, automatically set the `activeQuadrant` (or persona ID) instead of randomly defaulting or showing a selector for all quadrants.
- For a Single Male, it should route to "Alpha 教官".

### Task 3: Backend Prompt Alignment

**Files:**
- Modify: `d:\project\Cyber_Wingman\cyber_wingman\agent\context.py` (or wherever the `system_prompt` is resolved based on the quadrant).

**Step 1: Ensure Prompt Mapping**
- Make sure the backend correctly receives the `quadrant` parameter from the frontend and loads the exact markdown file (e.g., `prompt\Alpha 教官 (男-单身).md`).
- Ensure the API handles it without errors.

### Task 4: Global UI consistency

**Files:**
- Modify: Any other stray pages (like login modal) if necessary to match the dark cyber theme.
- Ensure `globals.css` already has all required styles (the `scanline` and `grid-bg` from `code.html` might need to be explicitly added to `globals.css` if not already merged during the index migration).

