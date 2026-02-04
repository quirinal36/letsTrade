import { createClient } from "@/lib/supabase/server";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

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

export default async function DashboardPage() {
  const summary = await getPortfolioSummary();

  const stats = [
    {
      title: "총 자산",
      value: `₩${summary.totalValue.toLocaleString()}`,
      icon: "💰",
    },
    {
      title: "총 손익",
      value: `${summary.totalProfit >= 0 ? "+" : ""}₩${summary.totalProfit.toLocaleString()}`,
      icon: summary.totalProfit >= 0 ? "📈" : "📉",
      color: summary.totalProfit >= 0 ? "text-green-600" : "text-red-600",
    },
    {
      title: "수익률",
      value: `${summary.profitRate >= 0 ? "+" : ""}${summary.profitRate.toFixed(2)}%`,
      icon: "📊",
      color: summary.profitRate >= 0 ? "text-green-600" : "text-red-600",
    },
    {
      title: "보유 종목",
      value: `${summary.positionCount}개`,
      icon: "📋",
    },
    {
      title: "오늘 거래",
      value: `${summary.todayTradeCount}건`,
      icon: "🔄",
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">대시보드</h2>
        <p className="text-gray-500 dark:text-gray-400">
          자동매매 현황을 한눈에 확인하세요
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
        {stats.map((stat) => (
          <Card key={stat.title}>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-gray-500">
                {stat.title}
              </CardTitle>
              <span className="text-xl">{stat.icon}</span>
            </CardHeader>
            <CardContent>
              <p className={`text-2xl font-bold ${stat.color || ""}`}>
                {stat.value}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Placeholder sections */}
      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>최근 거래</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-500">거래 내역이 없습니다.</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>활성 전략</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-500">활성화된 전략이 없습니다.</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
