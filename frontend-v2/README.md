# Signal-verse Frontend v2

This is the new, rebuilt frontend for the Signal-verse application. It is a modern, professional, and feature-rich dashboard for viewing and filtering trading signals.

## Getting Started

To get a local copy up and running, follow these simple steps.

### Prerequisites

*   Node.js (v18 or later)
*   npm, yarn, or pnpm

### Installation

1.  Clone the repo
    ```sh
    git clone https://your-repo-url.com
    ```
2.  Navigate to the `frontend-v2` directory
    ```sh
    cd frontend-v2
    ```
3.  Install NPM packages
    ```sh
    npm install
    ```
4.  Create a `.env.local` file in the root of the `frontend-v2` directory and add your Supabase credentials:
    ```env
    NEXT_PUBLIC_SUPABASE_URL=YOUR_SUPABASE_URL
    NEXT_PUBLIC_SUPABASE_ANON_KEY=YOUR_SUPABASE_ANON_KEY
    ```

### Running the Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result. The main dashboard is available at [http://localhost:3000/dashboard](http://localhost:3000/dashboard).

## Features

*   **Modern and Professional UI:** A complete redesign of the frontend using Next.js, TypeScript, and Shadcn/UI for a clean and professional look and feel.
*   **Advanced Filtering:** A powerful filtering system that allows you to filter signals by:
    *   Symbol
    *   Scanner Type
    *   Timeframe
    *   Status
    *   Signal Code Combinations (with "AND" logic)
*   **Real-time Updates:** The dashboard uses Supabase real-time subscriptions to show new signals as they arrive, without needing to refresh the page.
*   **Pagination:** The data table is paginated to handle a large number of signals efficiently.
*   **Error Handling:** The application has improved error handling and displays user-friendly messages when things go wrong.

## Technologies Used

*   [Next.js](https://nextjs.org/) - React framework for production.
*   [React](https://reactjs.org/) - A JavaScript library for building user interfaces.
*   [TypeScript](https://www.typescriptlang.org/) - A typed superset of JavaScript that compiles to plain JavaScript.
*   [Tailwind CSS](https://tailwindcss.com/) - A utility-first CSS framework for rapid UI development.
*   [Shadcn/UI](https://ui.shadcn.com/) - A collection of re-usable components built using Radix UI and Tailwind CSS.
*   [Supabase](https://supabase.io/) - The open source Firebase alternative.

## Folder Structure

```
frontend-v2/
├── src/
│   ├── app/
│   │   ├── dashboard/
│   │   │   ├── page.tsx         # Main dashboard page
│   │   │   ├── Filters.tsx      # Filters component
│   │   │   ├── DataTable.tsx    # Data table component
│   │   │   ├── Pagination.tsx   # Pagination component
│   │   │   └── ...
│   │   ├── layout.tsx         # Root layout
│   │   └── page.tsx           # Home page
│   ├── components/
│   │   └── ui/                # Shadcn/UI components
│   └── lib/
│       ├── supabaseClient.ts  # Supabase client configuration
│       └── filter-options.ts  # Static options for the filters
├── .env.local               # Environment variables
├── next.config.ts           # Next.js configuration
├── package.json             # Project dependencies
└── ...
```

## Backend

The backend for this application is located in the `backend` directory of the root project. It is a Python application that uses websockets to scan for signals and insert them into the Supabase database. The `fawda_scanner.py` file contains the main logic for signal generation.