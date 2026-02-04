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
import { format } from "date-fns";
import { ko } from "date-fns/locale";

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

async function getTrades(): Promise<Trade[]> {
  const supabase = await createClient();
  const { data, error } = await supabase
    .from("trades")
    .select("*")
    .order("created_at", { ascending: false })
    .limit(100);

  if (error) {
    console.error("Trades fetch error:", error);
    return [];
  }

  return data || [];
}

function getStatusBadge(status: string) {
  switch (status) {
    case "executed":
      return <Badge variant="default">체결</Badge>;
    case "partial":
      return <Badge variant="secondary">부분체결</Badge>;
    case "pending":
      return <Badge variant="outline">대기</Badge>;
    case "cancelled":
      return <Badge variant="destructive">취소</Badge>;
    case "rejected":
      return <Badge variant="destructive">거부</Badge>;
    default:
      return <Badge variant="outline">{status}</Badge>;
  }
}

export default async function TradesPage() {
  const trades = await getTrades();

  const buyCount = trades.filter((t) => t.order_type === "buy").length;
  const sellCount = trades.filter((t) => t.order_type === "sell").length;
  const executedCount = trades.filter((t) => t.status === "executed").length;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">거래 내역</h2>
        <p className="text-gray-500">모든 거래 내역을 확인하세요</p>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">
              총 거래
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{trades.length}건</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">
              매수
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-blue-600">{buyCount}건</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">
              매도
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-red-600">{sellCount}건</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">
              체결 완료
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-green-600">{executedCount}건</p>
          </CardContent>
        </Card>
      </div>

      {/* Trades Table */}
      <Card>
        <CardHeader>
          <CardTitle>거래 목록</CardTitle>
        </CardHeader>
        <CardContent>
          {trades.length === 0 ? (
            <p className="py-8 text-center text-gray-500">
              거래 내역이 없습니다.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>일시</TableHead>
                  <TableHead>종목</TableHead>
                  <TableHead>유형</TableHead>
                  <TableHead className="text-right">주문수량</TableHead>
                  <TableHead className="text-right">주문가격</TableHead>
                  <TableHead className="text-right">체결수량</TableHead>
                  <TableHead className="text-right">체결가격</TableHead>
                  <TableHead>상태</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {trades.map((trade) => (
                  <TableRow key={trade.id}>
                    <TableCell>
                      <div>
                        <p className="font-medium">
                          {format(new Date(trade.created_at), "MM/dd", {
                            locale: ko,
                          })}
                        </p>
                        <p className="text-sm text-gray-500">
                          {format(new Date(trade.created_at), "HH:mm")}
                        </p>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div>
                        <p className="font-medium">{trade.stock_name}</p>
                        <p className="text-sm text-gray-500">
                          {trade.stock_code}
                        </p>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={
                          trade.order_type === "buy" ? "default" : "destructive"
                        }
                      >
                        {trade.order_type === "buy" ? "매수" : "매도"}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      {trade.quantity.toLocaleString()}주
                    </TableCell>
                    <TableCell className="text-right">
                      ₩{trade.price.toLocaleString()}
                    </TableCell>
                    <TableCell className="text-right">
                      {trade.executed_quantity.toLocaleString()}주
                    </TableCell>
                    <TableCell className="text-right">
                      {trade.executed_price
                        ? `₩${trade.executed_price.toLocaleString()}`
                        : "-"}
                    </TableCell>
                    <TableCell>{getStatusBadge(trade.status)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
