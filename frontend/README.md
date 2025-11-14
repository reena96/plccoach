# PLC Coach - Frontend Application

React frontend application for the AI-Powered PLC at Work Virtual Coach.

## Technology Stack

- **Vite 5** - Build tool and dev server
- **React 18** - UI library
- **TypeScript** - Type safety
- **Tailwind CSS** - Utility-first styling
- **React Router** - Client-side routing
- **React Query** - Server state management
- **Axios** - HTTP client

## Setup Instructions

### Prerequisites

- Node.js 18+ and npm
- Backend API service running on `http://localhost:8000`

### Installation

1. Install dependencies:
   ```bash
   npm install
   ```

2. Environment variables are already configured in `.env`

## Development

### Start Development Server

```bash
npm run dev
```

Opens at `http://localhost:5173` with Hot Module Replacement (HMR).

### Build for Production

```bash
npm run build
```

Generates static files in `dist/` folder.

## Key Features

- **OAuth Login**: Google and Clever SSO integration
- **Session Management**: httpOnly cookies managed by backend
- **Protected Routes**: Automatic redirect to login if not authenticated
- **Responsive Design**: Mobile, tablet, and desktop support

## Environment Variables

| Variable | Default |
|----------|---------|
| `VITE_API_BASE_URL` | `http://localhost:8000` |

## Troubleshooting

- Ensure backend is running on port 8000
- Check browser console for errors
- Verify dependencies are installed
