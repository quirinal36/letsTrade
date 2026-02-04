import { createClient } from "@/lib/supabase/server";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";

interface Position {
  id: number;
  stock_code: string;
  stock_name: string;
  quantity: number;
  avg_price: number;
  current_price: number;
  total_cost: number;
  market_value: number;
  profit_loss: number;
  profit_loss_rate: number;
}

async function getPortfolio(): Promise<Position[]> {
  const supabase = await createClient();
  const { data, error } = await supabase
    .from("portfolio")
    .select("*")
    .order("market_value", { ascending: false });

  if (error) {
    console.error("Portfolio fetch error:", error);
    return [];
  }

  return data || [];
}

export default async function PortfolioPage() {
  const portfolio = await getPortfolio();

  const totalValue = portfolio.reduce((sum, p) => sum + p.market_value, 0);
  const totalCost = portfolio.reduce((sum, p) => sum + p.total_cost, 0);
  const totalProfit = portfolio.reduce((sum, p) => sum + p.profit_loss, 0);
  const totalProfitRate = totalCost > 0 ? (totalProfit / totalCost) * 100 : 0;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">포트폴리오</h2>
        <p className="text-gray-500">보유 종목 현황을 확인하세요</p>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">
              총 평가금액
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">₩{totalValue.toLocaleString()}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">
              총 매입금액
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">₩{totalCost.toLocaleString()}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">
              총 평가손익
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p
              className={`text-2xl font-bold ${
                totalProfit >= 0 ? "text-green-600" : "text-red-600"
              }`}
            >
              {totalProfit >= 0 ? "+" : ""}₩{totalProfit.toLocaleString()}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">
              총 수익률
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p
              className={`text-2xl font-bold ${
                totalProfitRate >= 0 ? "text-green-600" : "text-red-600"
              }`}
            >
              {totalProfitRate >= 0 ? "+" : ""}
              {totalProfitRate.toFixed(2)}%
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Portfolio Table */}
      <Card>
        <CardHeader>
          <CardTitle>보유 종목</CardTitle>
        </CardHeader>
        <CardContent>
          {portfolio.length === 0 ? (
            <p className="py-8 text-center text-gray-500">
              보유 종목이 없습니다.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>종목</TableHead>
                  <TableHead className="text-right">보유수량</TableHead>
                  <TableHead className="text-right">평균단가</TableHead>
                  <TableHead className="text-right">현재가</TableHead>
                  <TableHead className="text-right">평가금액</TableHead>
                  <TableHead className="text-right">손익</TableHead>
                  <TableHead className="text-right">수익률</TableHead>
                  <TableHead className="text-right">비중</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {portfolio.map((position) => {
                  const weight =
                    totalValue > 0
                      ? (position.market_value / totalValue) * 100
                      : 0;
                  return (
                    <TableRow key={position.id}>
                      <TableCell>
                        <div>
                          <p className="font-medium">{position.stock_name}</p>
                          <p className="text-sm text-gray-500">
                            {position.stock_code}
                          </p>
                        </div>
                      </TableCell>
                      <TableCell className="text-right">
                        {position.quantity.toLocaleString()}주
                      </TableCell>
                      <TableCell className="text-right">
                        ₩{position.avg_price.toLocaleString()}
                      </TableCell>
                      <TableCell className="text-right">
                        ₩{position.current_price.toLocaleString()}
                      </TableCell>
                      <TableCell className="text-right">
                        ₩{position.market_value.toLocaleString()}
                      </TableCell>
                      <TableCell
                        className={`text-right ${
                          position.profit_loss >= 0
                            ? "text-green-600"
                            : "text-red-600"
                        }`}
                      >
                        {position.profit_loss >= 0 ? "+" : ""}₩
                        {position.profit_loss.toLocaleString()}
                      </TableCell>
                      <TableCell className="text-right">
                        <Badge
                          variant={
                            position.profit_loss_rate >= 0
                              ? "default"
                              : "destructive"
                          }
                        >
                          {position.profit_loss_rate >= 0 ? "+" : ""}
                          {position.profit_loss_rate.toFixed(2)}%
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        {weight.toFixed(1)}%
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
