import { HealthStatus } from "@/components/HealthStatus";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { MessageSquare } from "lucide-react";

export default function HomePage(): React.JSX.Element {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-8 p-8">
      <div className="text-center">
        <h1 className="text-3xl font-bold tracking-tight">EK-RAG Console</h1>
        <p className="mt-2 text-muted-foreground">
          Local-first enterprise knowledge assistant. This page confirms
          connectivity to the EKCP gateway.
        </p>
      </div>
      <HealthStatus />
      <Button asChild>
        <Link href="/chat">
          <MessageSquare className="h-4 w-4" aria-hidden />
          Open Chat
        </Link>
      </Button>
    </main>
  );
}
