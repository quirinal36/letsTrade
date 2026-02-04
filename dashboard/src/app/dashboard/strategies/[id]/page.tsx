import { notFound } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { format } from "date-fns";
import { ko } from "date-fns/locale";

interface Props {
  params: Promise<{ id: string }>;
}

async function getStrategy(id: number) {
  const supabase = await createClient();
  const { data, error } = await supabase
    .from("strategies")
    .select("*")
    .eq("id", id)
    .single();

  if (error) return null;
  return data;
}

async function getRecentSignals(strategyId: number) {
  const supabase = await createClient();
  const { data } = await supabase
    .from("signals")
    .select("*")
    .eq("strategy_id", strategyId)
    .order("created_at", { ascending: false })
    .limit(20);

  return data || [];
}

export default async function StrategyDetailPage({ params }: Props) {
  const { id } = await params;
  const strategyId = parseInt(id);

  if (isNaN(strategyId)) {
    notFound();
  }

  const strategy = await getStrategy(strategyId);
  if (!strategy) {
    notFound();
  }

  const signals = await getRecentSignals(strategyId);

  const getTypeLabel = (type: string) => {
    const types: Record<string, string> = {
      ma_crossover: "이동평균 교차",
      rsi_oversold: "RSI 과매도",
      bollinger_bands: "볼린저밴드",
      macd: "MACD",
      custom: "커스텀",
    };
    return types[type] || type;
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-2xl font-bold">{strategy.name}</h2>
            <Badge variant={strategy.is_active ? "default" : "secondary"}>
              {strategy.is_active ? "활성" : "비활성"}
            </Badge>
          </div>
          <p className="text-gray-500">{strategy.description}</p>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Strategy Info */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>전략 정보</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-500">전략 유형</p>
                <p className="font-medium">
                  {getTypeLabel(strategy.strategy_type)}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500">우선순위</p>
                <p className="font-medium">{strategy.priority}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">최대 투자금</p>
                <p className="font-medium">
                  {strategy.max_investment
                    ? `₩${strategy.max_investment.toLocaleString()}`
                    : "제한 없음"}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500">대상 종목</p>
                <p className="font-medium">
                  {strategy.stock_codes || "전체"}
                </p>
              </div>
            </div>

            <Separator />

            <div>
              <p className="text-sm font-medium text-gray-500 mb-2">
                리스크 설정
              </p>
              <div className="grid grid-cols-2 gap-4">
                <div className="p-3 bg-red-50 dark:bg-red-950 rounded-lg">
                  <p className="text-sm text-red-600">손절선</p>
                  <p className="text-xl font-bold text-red-600">
                    {strategy.max_loss_rate
                      ? `-${strategy.max_loss_rate}%`
                      : "미설정"}
                  </p>
                </div>
                <div className="p-3 bg-green-50 dark:bg-green-950 rounded-lg">
                  <p className="text-sm text-green-600">익절선</p>
                  <p className="text-xl font-bold text-green-600">
                    {strategy.take_profit_rate
                      ? `+${strategy.take_profit_rate}%`
                      : "미설정"}
                  </p>
                </div>
              </div>
            </div>

            {strategy.parameters && Object.keys(strategy.parameters).length > 0 && (
              <>
                <Separator />
                <div>
                  <p className="text-sm font-medium text-gray-500 mb-2">
                    파라미터
                  </p>
                  <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3">
                    <pre className="text-sm overflow-auto">
                      {JSON.stringify(strategy.parameters, null, 2)}
                    </pre>
                  </div>
                </div>
              </>
            )}
          </CardContent>
        </Card>

        {/* Stats */}
        <Card>
          <CardHeader>
            <CardTitle>통계</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="text-sm text-gray-500">총 시그널</p>
              <p className="text-2xl font-bold">{signals.length}건</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">실행된 시그널</p>
              <p className="text-2xl font-bold text-green-600">
                {signals.filter((s) => s.status === "executed").length}건
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500">대기 중 시그널</p>
              <p className="text-2xl font-bold text-yellow-600">
                {signals.filter((s) => s.status === "pending").length}건
              </p>
            </div>
            <Separator />
            <div>
              <p className="text-sm text-gray-500">생성일</p>
              <p className="font-medium">
                {format(new Date(strategy.created_at), "yyyy-MM-dd HH:mm", {
                  locale: ko,
                })}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500">수정일</p>
              <p className="font-medium">
                {format(new Date(strategy.updated_at), "yyyy-MM-dd HH:mm", {
                  locale: ko,
                })}
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Signals */}
      <Card>
        <CardHeader>
          <CardTitle>최근 시그널</CardTitle>
        </CardHeader>
        <CardContent>
          {signals.length === 0 ? (
            <p className="py-8 text-center text-gray-500">
              아직 생성된 시그널이 없습니다.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>일시</TableHead>
                  <TableHead>종목</TableHead>
                  <TableHead>유형</TableHead>
                  <TableHead className="text-right">가격</TableHead>
                  <TableHead className="text-right">강도</TableHead>
                  <TableHead>상태</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {signals.map((signal) => (
                  <TableRow key={signal.id}>
                    <TableCell>
                      {format(new Date(signal.created_at), "MM/dd HH:mm")}
                    </TableCell>
                    <TableCell>
                      <div>
                        <p className="font-medium">{signal.stock_name}</p>
                        <p className="text-sm text-gray-500">
                          {signal.stock_code}
                        </p>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={
                          signal.signal_type === "buy"
                            ? "default"
                            : signal.signal_type === "sell"
                            ? "destructive"
                            : "secondary"
                        }
                      >
                        {signal.signal_type === "buy"
                          ? "매수"
                          : signal.signal_type === "sell"
                          ? "매도"
                          : "홀드"}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      ₩{signal.price.toLocaleString()}
                    </TableCell>
                    <TableCell className="text-right">
                      {signal.strength ? `${(signal.strength * 100).toFixed(0)}%` : "-"}
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={
                          signal.status === "executed"
                            ? "default"
                            : signal.status === "pending"
                            ? "outline"
                            : "secondary"
                        }
                      >
                        {signal.status === "executed"
                          ? "실행됨"
                          : signal.status === "pending"
                          ? "대기"
                          : signal.status}
                      </Badge>
                    </TableCell>
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
