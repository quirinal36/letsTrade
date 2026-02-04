"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { usePortfolioRealtime, useTradesRealtime } from "@/hooks/use-realtime";

interface LiveStatsProps {
  initialStats: {
    totalValue: number;
    totalProfit: number;
    profitRate: number;
    positionCount: number;
    todayTradeCount: number;
  };
}

export function LiveStats({ initialStats }: LiveStatsProps) {
  const router = useRouter();
  const [stats, setStats] = useState(initialStats);
  const [isUpdating, setIsUpdating] = useState(false);

  // Subscribe to portfolio changes
  usePortfolioRealtime({
    onPortfolioChange: () => {
      // Refresh the page data when portfolio changes
      setIsUpdating(true);
      router.refresh();
      setTimeout(() => setIsUpdating(false), 1000);
    },
    onPositionUpdate: () => {
      setIsUpdating(true);
      router.refresh();
      setTimeout(() => setIsUpdating(false), 1000);
    },
  });

  // Subscribe to new trades
  useTradesRealtime({
    onNewTrade: () => {
      setStats((prev) => ({
        ...prev,
        todayTradeCount: prev.todayTradeCount + 1,
      }));
      setIsUpdating(true);
      router.refresh();
      setTimeout(() => setIsUpdating(false), 1000);
    },
  });

  // Update stats when initialStats changes (from server refresh)
  useEffect(() => {
    setStats(initialStats);
  }, [initialStats]);

  const statItems = [
    {
      title: "총 자산",
      value: `₩${stats.totalValue.toLocaleString()}`,
      icon: "💰",
    },
    {
      title: "총 손익",
      value: `${stats.totalProfit >= 0 ? "+" : ""}₩${stats.totalProfit.toLocaleString()}`,
      icon: stats.totalProfit >= 0 ? "📈" : "📉",
      color: stats.totalProfit >= 0 ? "text-green-600" : "text-red-600",
    },
    {
      title: "수익률",
      value: `${stats.profitRate >= 0 ? "+" : ""}${stats.profitRate.toFixed(2)}%`,
      icon: "📊",
      color: stats.profitRate >= 0 ? "text-green-600" : "text-red-600",
    },
    {
      title: "보유 종목",
      value: `${stats.positionCount}개`,
      icon: "📋",
    },
    {
      title: "오늘 거래",
      value: `${stats.todayTradeCount}건`,
      icon: "🔄",
    },
  ];

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
      {statItems.map((stat) => (
        <Card
          key={stat.title}
          className={`transition-all duration-300 ${isUpdating ? "ring-2 ring-blue-500/50" : ""}`}
        >
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
  );
}
