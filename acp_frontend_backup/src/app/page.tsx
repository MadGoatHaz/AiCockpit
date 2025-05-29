// acp_frontend/src/app/page.tsx
import { redirect } from 'next/navigation';

export default function HomePage() {
  redirect('/interact');
  return null; // Keep Next.js happy, redirect should happen before render
}
