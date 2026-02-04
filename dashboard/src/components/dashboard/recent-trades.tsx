"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useTradesRealtime } from "@/hooks/use-realtime";
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

interface RecentTradesProps {
  initialTrades: Trade[];
}

export function RecentTrades({ initialTrades }: RecentTradesProps) {
  const router = useRouter();
  const [trades, setTrades] = useState<Trade[]>(initialTrades);
  const [newTradeIds, setNewTradeIds] = useState<Set<number>>(new Set());

  useTradesRealtime({
    onNewTrade: (trade) => {
      setTrades((prev) => [trade, ...prev].slice(0, 5));
      setNewTradeIds((prev) => new Set(prev).add(trade.id));

      // Remove highlight after animation
      setTimeout(() => {
        setNewTradeIds((prev) => {
          const next = new Set(prev);
          next.delete(trade.id);
          return next;
        });
      }, 3000);
    },
    onTradeUpdate: ({ new: updatedTrade }) => {
      setTrades((prev) =>
        prev.map((t) => (t.id === updatedTrade.id ? updatedTrade : t))
      );
    },
  });

  useEffect(() => {
    setTrades(initialTrades);
  }, [initialTrades]);

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
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          최근 거래
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {trades.length === 0 ? (
          <p className="text-sm text-gray-500">거래 내역이 없습니다.</p>
        ) : (
          <div className="space-y-3">
            {trades.map((trade) => (
              <div
                key={trade.id}
                className={`flex items-center justify-between p-3 rounded-lg border transition-all duration-500 ${
                  newTradeIds.has(trade.id)
                    ? "bg-blue-50 border-blue-200 dark:bg-blue-900/20 dark:border-blue-800"
                    : "bg-white dark:bg-gray-800"
                }`}
              >
                <div className="flex items-center gap-3">
                  <Badge
                    variant={trade.order_type === "buy" ? "default" : "destructive"}
                  >
                    {trade.order_type === "buy" ? "매수" : "매도"}
                  </Badge>
                  <div>
                    <p className="font-medium">{trade.stock_name}</p>
                    <p className="text-xs text-gray-500">
                      {format(new Date(trade.created_at), "HH:mm", { locale: ko })}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="font-medium">
                    {trade.quantity.toLocaleString()}주
                  </p>
                  <p className="text-xs text-gray-500">
                    ₩{trade.price.toLocaleString()}
                  </p>
                </div>
                <div>{getStatusBadge(trade.status)}</div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
