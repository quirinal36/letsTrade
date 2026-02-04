"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ChatInterface } from "@/components/strategy/chat-interface";
import { StrategyPreview } from "@/components/strategy/strategy-preview";
import { createClient } from "@/lib/supabase/client";
import type { Strategy } from "@/lib/ai/strategy-tools";

export default function NewStrategyPage() {
  const router = useRouter();
  const [strategy, setStrategy] = useState<Strategy | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  const handleStrategyGenerated = (newStrategy: Strategy) => {
    setStrategy(newStrategy);
  };

  const handleSave = async () => {
    if (!strategy) return;

    setIsSaving(true);
    try {
      const supabase = createClient();
      const { error } = await supabase.from("strategies").insert({
        name: strategy.name,
        description: strategy.description,
        strategy_type: strategy.strategy_type,
        parameters: strategy.parameters || {},
        stock_codes: strategy.stock_codes || null,
        max_investment: strategy.max_investment || null,
        max_loss_rate: strategy.max_loss_rate || null,
        take_profit_rate: strategy.take_profit_rate || null,
        is_active: false,
        priority: 0,
      });

      if (error) {
        console.error("Failed to save strategy:", error);
        alert("전략 저장에 실패했습니다: " + error.message);
        return;
      }

      router.push("/dashboard/strategies");
      router.refresh();
    } catch (error) {
      console.error("Error saving strategy:", error);
      alert("전략 저장 중 오류가 발생했습니다.");
    } finally {
      setIsSaving(false);
    }
  };

  const handleClear = () => {
    setStrategy(null);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/dashboard/strategies">
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div>
          <h2 className="text-2xl font-bold">새 전략 만들기</h2>
          <p className="text-gray-500">AI와 대화하며 매매 전략을 생성하세요</p>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2 h-[calc(100vh-220px)]">
        <ChatInterface onStrategyGenerated={handleStrategyGenerated} />
        <StrategyPreview
          strategy={strategy}
          onSave={handleSave}
          onClear={handleClear}
          isSaving={isSaving}
        />
      </div>
    </div>
  );
}
