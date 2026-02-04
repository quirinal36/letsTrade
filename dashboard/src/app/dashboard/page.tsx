import { createClient } from "@/lib/supabase/server";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LiveStats } from "@/components/dashboard/live-stats";
import { RecentTrades } from "@/components/dashboard/recent-trades";

interface Trade {
  id: number;
  order_no: string;
  stock_code: string;
  stock_name: string;
  order_type: "buy" | "sell";
  status: string;
  quantity: number;
  price: number;
  executed_quantity: number;
  executed_price: number | null;
  executed_at: string | null;
  created_at: string;
}

async function getPortfolioSummary() {
  const supabase = await createClient();

  const { data: portfolio } = await supabase
    .from("portfolio")
    .select("*");

  const { data: todayTrades } = await supabase
    .from("trades")
    .select("*")
    .gte("created_at", new Date().toISOString().split("T")[0]);

  const totalValue = portfolio?.reduce((sum, p) => sum + (p.market_value || 0), 0) || 0;
  const totalProfit = portfolio?.reduce((sum, p) => sum + (p.profit_loss || 0), 0) || 0;
  const profitRate = totalValue > 0 ? (totalProfit / (totalValue - totalProfit)) * 100 : 0;

  return {
    totalValue,
    totalProfit,
    profitRate,
    positionCount: portfolio?.length || 0,
    todayTradeCount: todayTrades?.length || 0,
  };
}

async function getRecentTrades(): Promise<Trade[]> {
  const supabase = await createClient();

  const { data } = await supabase
    .from("trades")
    .select("*")
    .order("created_at", { ascending: false })
    .limit(5);

  return data || [];
}

async function getActiveStrategies() {
  const supabase = await createClient();

  const { data } = await supabase
    .from("strategies")
    .select("*")
    .eq("is_active", true)
    .limit(5);

  return data || [];
}

export default async function DashboardPage() {
  const [summary, recentTrades, activeStrategies] = await Promise.all([
    getPortfolioSummary(),
    getRecentTrades(),
    getActiveStrategies(),
  ]);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">대시보드</h2>
        <p className="text-gray-500 dark:text-gray-400">
          자동매매 현황을 한눈에 확인하세요
        </p>
      </div>

      {/* Live Stats Grid */}
      <LiveStats initialStats={summary} />

      {/* Recent Trades & Active Strategies */}
      <div className="grid gap-6 md:grid-cols-2">
        <RecentTrades initialTrades={recentTrades} />

        <Card>
          <CardHeader>
            <CardTitle>활성 전략</CardTitle>
          </CardHeader>
          <CardContent>
            {activeStrategies.length === 0 ? (
              <p className="text-sm text-gray-500">활성화된 전략이 없습니다.</p>
            ) : (
              <div className="space-y-3">
                {activeStrategies.map((strategy: { id: number; name: string; strategy_type: string }) => (
                  <div
                    key={strategy.id}
                    className="flex items-center justify-between p-3 rounded-lg border bg-white dark:bg-gray-800"
                  >
                    <div>
                      <p className="font-medium">{strategy.name}</p>
                      <p className="text-xs text-gray-500">{strategy.strategy_type}</p>
                    </div>
                    <span className="relative flex h-2 w-2">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                    </span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
