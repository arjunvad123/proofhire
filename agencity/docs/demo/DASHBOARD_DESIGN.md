# Product Specifications & Design Criteria

> [!NOTE]
> This document assumes the role of a source of truth for design and functionality, derived from `app/company-form/page.tsx` and `app/dashboard/page.tsx`.

## 1. Design Criteria

### 1.1 Visual Identity & Color Palette

The application uses a **clean, professional, and data-focused** aesthetic. High contrast is used for readability, with a "premium" feel achieved through whitespace and subtle shadows.

-   **Primary Brand Color**:
    -   Blue: `text-blue-500` / `bg-blue-600` / `border-blue-500`
    -   Used for: Primary actions (buttons), active states, key highlights, focus rings.
-   **Neutrals**:
    -   **Black** (`text-black`, `bg-black`): Primary headings, strong visual elements.
    -   **White** (`bg-white`): Card backgrounds, main content areas.
    -   **Gray Scale**:
        -   `bg-gray-50`: App background, input backgrounds.
        -   `text-gray-900`: Secondary headings.
        -   `text-gray-600`: Body text, secondary information.
        -   `text-gray-500` / `text-gray-400`: Metadata, placeholders.
        -   `border-gray-200` / `border-gray-300`: Dividers, borders.
-   **Semantic / Status Colors**:
    -   **Green** (`text-green-700`, `bg-green-50`): Success, High scores (≥80%), "Running" status.
    -   **Yellow** (`text-yellow-700`, `bg-yellow-50`): Warnings, Medium scores (60-79%), "Provisioning" status.
    -   **Red** (`text-red-700`, `bg-red-50`): Errors, Low scores (<60%), "Error" status.

### 1.2 Typography

Typography is used to establish hierarchy and clarity.

-   **Font Family**: Default system sans-serif stack (likely Inter or similar via Tailwind defaults).
-   **Headings**:
    -   **H1**: `text-3xl` to `text-5xl`, `font-bold`, `tracking-tight`, `leading-tight`.
    -   **H2**: `text-xl`, `font-semibold`.
    -   **H3**: `font-medium`.
-   **Body**: `text-base` usually, `text-sm` for table data and secondary info. `text-xs` for labels and badges.
-   **Monospace**: `font-mono` used for IDs (Session IDs, Candidate IDs).

### 1.3 Layout & Spacing

-   **Container Width**: `max-w-7xl mx-auto` for main dashboard content.
-   **Page Structure**:
    -   **Split View (Onboarding)**: 50% Content / 50% Visual on large screens (`lg:flex-row`).
    -   **Standard Dashboard**: Single column, centered content with vertical stacking.
-   **Padding/Margins**: Generous spacing (`p-6`, `p-8`, `p-12`) to avoid clutter.
-   **Cards**:
    -   Background: `bg-white`
    -   Border Radius: `rounded-lg` or `rounded-2xl` for more modern feel (onboarding).
    -   Shadow: `shadow` or `shadow-xl`.

### 1.4 UI Components

-   **Buttons**:
    -   Primary: `bg-black text-white` (Onboarding) or `bg-blue-600 text-white` (Dashboard).
    -   Hover States: `hover:bg-gray-900` or `hover:bg-blue-700`.
    -   Rounding: `rounded-2xl` (Onboarding) vs `rounded-lg` (Dashboard) - *Note: Trend seems to be moving towards softer `rounded-2xl` for higher-level interactions*.
    -   Loading State: Spinner + "Submitting..." text.
-   **Inputs**:
    -   Style: `px-5 py-3`, `rounded-2xl` (Onboarding) or `rounded-lg`, `border-gray-200`, `bg-gray-50`.
    -   Focus: `focus:ring-2`, `focus:ring-blue-500/20`, `outline-none`.
-   **Badges**:
    -   Pill shape: `rounded-full`.
    -   Size: `px-2 py-1 text-xs font-medium`.
-   **Motion & Interaction**:
    -   **Framer Motion**: Used for smooth transitions between phases (`initial`, `animate`, `exit`) and micro-interactions (hover scales).
    -   **Transitions**: Standard Tailwind `transition-all duration-300`.

---

## 2. Product Specifications

### 2.1 Feature: Company Onboarding (Funnel)

**Goal**: Collect essential company information and job requirements to match with candidates.

**Flow**:
1.  **Phase 1: Company Profile**
    -   **Input**: Company Name (Text).
    -   **Input**: Website URL (Url).
    -   *Validation*: Both fields required.
2.  **Phase 2: Hiring Needs**
    -   **Input**: Job Description (Textarea).
    -   **Input**: File Upload (Resume/JD).
        -   *Constraints*: Max 5MB. Allowed types: `.pdf`, `.doc`, `.docx`, `.txt`.
        -   *UI*: Drag & drop area, progress indication, remove file option.
    -   *Validation*: Either text description OR file upload is required.
3.  **Completion & Success**
    -   **Action**: Save data to `startup_users` table in Supabase.
    -   **Action**: Upload file to `job-postings` bucket (if applicable).
    -   **Action**: Auto-redirect/Open link to Calendly for demo booking.
    -   **UI**: Success message, "Book Demo" fallback button, "Go to Dashboard" button.

**Data Model (inferred `startup_users`)**:
-   `user_id`: UUID (Foreign Key)
-   `company_name`: String
-   `website`: String
-   `hiring_for`: String (Text)
-   `job_posting_file_url`: String (Path)
-   `role`: 'founder' (default)
-   `onboarding_completed`: Boolean

### 2.2 Feature: Assessment Dashboard

**Goal**: View and search candidate assessment results.

**Key Components**:
1.  **Search & Autocomplete**
    -   **Function**: Real-time search by Candidate Name or Email.
    -   **Autocomplete**: Dropdown appears after 2 chars. Shows Name + Email. Keyboard navigation supported (`ArrowDown`, `ArrowUp`, `Enter`).
    -   **Multiple Results**: Handling for search terms matching multiple candidates.
2.  **Candidate Overview**
    -   Display basic info: Name, Email, ID, Registration Date.
3.  **Metrics Grid** (KPIs)
    -   **Total Sessions**: Count.
    -   **Avg Test Runs**: Number (Target: 2-4). Color-coded (Green/Yellow).
    -   **Avg Score**: 0-100. Color-coded (≥80 Green, 60-79 Yellow, <60 Red).
    -   **Pass Rate**: Percentage of passing runs.
    -   **AI Leverage Score**: Custom metric.
    -   **Validation Score**: Custom metric.
4.  **Session History Table**
    -   Columns: Session ID (truncated), Status (Badge), Test Runs, Last Score (Badge), Duration (calculated), Started At.
    -   Statuses: `running`, `stopped`, `provisioning`, `error`.
5.  **Visualizations**
    -   **Score Progression**: Bar/Timeline visualization showing score improvement over time.
6.  **Activity Feed**
    -   **Recent Commits**: List of latest code commits with messages and timestamps.

**API Integration Specs**:
-   `GET /api/dashboard/autocomplete?q={query}`: Returns `{ suggestions: [] }`.
-   `GET /api/dashboard/candidate?name={name}` OR `?candidateId={id}`: Returns Candidate Data Object OR Multiple Candidates Object.
