import Link from "next/link";
import { Plus, Sparkles } from "lucide-react";
import { createClient } from "@/lib/supabase/server";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { StrategyCard } from "./strategy-card";

interface Strategy {
  id: number;
  name: string;
  description: string | null;
  strategy_type: string;
  stock_codes: string | null;
  parameters: Record<string, any> | null;
  max_investment: number | null;
  max_loss_rate: number | null;
  take_profit_rate: number | null;
  is_active: boolean;
  priority: number;
  created_at: string;
  updated_at: string;
}

async function getStrategies(): Promise<Strategy[]> {
  const supabase = await createClient();
  const { data, error } = await supabase
    .from("strategies")
    .select("*")
    .order("priority", { ascending: false });

  if (error) {
    console.error("Strategies fetch error:", error);
    return [];
  }

  return data || [];
}

async function getSignalStats() {
  const supabase = await createClient();
  const { data } = await supabase
    .from("signals")
    .select("strategy_id, signal_type, status")
    .gte("created_at", new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString());

  return data || [];
}

export default async function StrategiesPage() {
  const strategies = await getStrategies();
  const signals = await getSignalStats();

  const activeCount = strategies.filter((s) => s.is_active).length;
  const totalSignals = signals.length;
  const executedSignals = signals.filter((s) => s.status === "executed").length;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">전략 관리</h2>
          <p className="text-gray-500">매매 전략을 관리하고 모니터링하세요</p>
        </div>
        <Link href="/dashboard/strategies/new">
          <Button className="gap-2">
            <Sparkles className="h-4 w-4" />
            AI로 전략 만들기
          </Button>
        </Link>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">
              전체 전략
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{strategies.length}개</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">
              활성 전략
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-green-600">{activeCount}개</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">
              7일간 시그널
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{totalSignals}건</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">
              실행된 시그널
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-blue-600">{executedSignals}건</p>
          </CardContent>
        </Card>
      </div>

      {/* Strategy List */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {strategies.length === 0 ? (
          <Card className="col-span-full">
            <CardContent className="py-8 text-center">
              <p className="text-gray-500">등록된 전략이 없습니다.</p>
              <p className="mt-2 text-sm text-gray-400">
                AI와 대화하며 나만의 매매 전략을 만들어보세요.
              </p>
              <Link href="/dashboard/strategies/new" className="inline-block mt-4">
                <Button className="gap-2">
                  <Sparkles className="h-4 w-4" />
                  첫 전략 만들기
                </Button>
              </Link>
            </CardContent>
          </Card>
        ) : (
          strategies.map((strategy) => {
            const strategySignals = signals.filter(
              (s) => s.strategy_id === strategy.id
            );
            return (
              <StrategyCard
                key={strategy.id}
                strategy={strategy}
                signalCount={strategySignals.length}
              />
            );
          })
        )}
      </div>
    </div>
  );
}
