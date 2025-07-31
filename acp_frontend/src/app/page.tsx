// acp_frontend/src/app/page.tsx
"use client";

import React from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ComputerIcon, CodeIcon } from "lucide-react";

export default function Home() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gradient-to-b from-background to-muted p-4">
      <div className="max-w-3xl w-full space-y-8 text-center">
        <h1 className="text-4xl font-bold tracking-tight sm:text-5xl md:text-6xl">
          Welcome to <span className="text-primary">AiCockpit</span>
        </h1>
        <p className="text-lg text-muted-foreground sm:text-xl">
          The revolutionary AI-collaborative development platform where VS Code becomes the "IDE hand" of your AI collaborator.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Button asChild size="lg">
            <Link href="/interact">
              <CodeIcon className="mr-2 h-5 w-5" />
              Start Coding
            </Link>
          </Button>
          <Button asChild variant="outline" size="lg">
            <Link href="/workspaces">
              <ComputerIcon className="mr-2 h-5 w-5" />
              View Workspaces
            </Link>
          </Button>
        </div>
        <div className="mt-12 p-6 bg-card rounded-lg border shadow-sm">
          <h2 className="text-2xl font-semibold mb-4">Get Started</h2>
          <p className="text-muted-foreground mb-4">
            AiCockpit provides containerized development environments that you can launch instantly. 
            Create a new workspace or select an existing one to start coding with AI assistance.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
            <div className="p-4 bg-muted rounded-lg">
              <h3 className="font-semibold mb-2">1. Create Workspace</h3>
              <p className="text-sm text-muted-foreground">Set up a new development environment with your preferred tools</p>
            </div>
            <div className="p-4 bg-muted rounded-lg">
              <h3 className="font-semibold mb-2">2. Launch IDE</h3>
              <p className="text-sm text-muted-foreground">Open the web-based IDE with full terminal access</p>
            </div>
            <div className="p-4 bg-muted rounded-lg">
              <h3 className="font-semibold mb-2">3. Code with AI</h3>
              <p className="text-sm text-muted-foreground">Get AI assistance for coding, debugging, and more</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
