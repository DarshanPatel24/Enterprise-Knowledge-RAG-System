import Link from "next/link";
import { ArrowLeft } from "lucide-react";

import { SettingsForm } from "@/components/SettingsForm";
import { Button } from "@/components/ui/button";

export default function SettingsPage(): React.JSX.Element {
  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col gap-6 p-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold tracking-tight">Settings</h1>
        <Button asChild variant="ghost" size="sm">
          <Link href="/chat">
            <ArrowLeft className="h-4 w-4" aria-hidden />
            Back to chat
          </Link>
        </Button>
      </div>
      <SettingsForm />
    </main>
  );
}
