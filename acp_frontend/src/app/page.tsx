// acp_frontend/src/app/page.tsx
import { redirect } from 'next/navigation';

export default function HomePage() {
  // Redirect to the main application page, e.g., the "interact" (Workspaces) page
  redirect('/interact');
  // Or, you could return a simple landing page component here if you prefer
  // return <LandingPage />;
}
