"use client";

import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/button";

interface HeaderProps {
  user: {
    email?: string;
  } | null;
}

export function Header({ user }: HeaderProps) {
  const router = useRouter();
  const supabase = createClient();

  const handleLogout = async () => {
    await supabase.auth.signOut();
    router.push("/login");
    router.refresh();
  };

  return (
    <header className="fixed left-64 right-0 top-0 z-30 h-16 border-b bg-white dark:bg-gray-900">
      <div className="flex h-full items-center justify-between px-6">
        <div>
          <h1 className="text-lg font-semibold">자동매매 대시보드</h1>
        </div>
        <div className="flex items-center gap-4">
          {user && (
            <>
              <span className="text-sm text-gray-600 dark:text-gray-400">
                {user.email}
              </span>
              <Button variant="outline" size="sm" onClick={handleLogout}>
                로그아웃
              </Button>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
