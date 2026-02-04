"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  Legend,
} from "recharts";

// Sample data - replace with real data from API
const dailyData = [
  { date: "01/27", value: 10000000, profit: 0 },
  { date: "01/28", value: 10150000, profit: 150000 },
  { date: "01/29", value: 10080000, profit: -70000 },
  { date: "01/30", value: 10320000, profit: 240000 },
  { date: "01/31", value: 10280000, profit: -40000 },
  { date: "02/01", value: 10450000, profit: 170000 },
  { date: "02/02", value: 10520000, profit: 70000 },
  { date: "02/03", value: 10480000, profit: -40000 },
  { date: "02/04", value: 10650000, profit: 170000 },
];

const monthlyData = [
  { month: "2025/09", value: 8500000, profit: -200000 },
  { month: "2025/10", value: 9200000, profit: 700000 },
  { month: "2025/11", value: 9100000, profit: -100000 },
  { month: "2025/12", value: 9800000, profit: 700000 },
  { month: "2026/01", value: 10200000, profit: 400000 },
  { month: "2026/02", value: 10650000, profit: 450000 },
];

const tradeStats = [
  { name: "매수", count: 45 },
  { name: "매도", count: 38 },
  { name: "체결", count: 78 },
  { name: "취소", count: 5 },
];

export default function AnalyticsPage() {
  const [period, setPeriod] = useState("daily");

  const data = period === "daily" ? dailyData : monthlyData;
  const xKey = period === "daily" ? "date" : "month";

  // Calculate stats
  const totalProfit = data.reduce((sum, d) => sum + d.profit, 0);
  const winDays = data.filter((d) => d.profit > 0).length;
  const lossDays = data.filter((d) => d.profit < 0).length;
  const winRate = data.length > 0 ? (winDays / data.length) * 100 : 0;
  const avgProfit = data.length > 0 ? totalProfit / data.length : 0;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">수익률 분석</h2>
        <p className="text-gray-500">투자 성과를 분석하세요</p>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">
              누적 손익
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
              승률
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{winRate.toFixed(1)}%</p>
            <p className="text-sm text-gray-500">
              {winDays}승 {lossDays}패
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">
              평균 일 손익
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p
              className={`text-2xl font-bold ${
                avgProfit >= 0 ? "text-green-600" : "text-red-600"
              }`}
            >
              {avgProfit >= 0 ? "+" : ""}₩{Math.round(avgProfit).toLocaleString()}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">
              현재 자산
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">
              ₩{data[data.length - 1]?.value.toLocaleString() || 0}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Asset Chart */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>자산 추이</CardTitle>
              <Tabs value={period} onValueChange={setPeriod}>
                <TabsList>
                  <TabsTrigger value="daily">일별</TabsTrigger>
                  <TabsTrigger value="monthly">월별</TabsTrigger>
                </TabsList>
              </Tabs>
            </div>
          </CardHeader>
          <CardContent>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey={xKey} />
                  <YAxis
                    tickFormatter={(value) =>
                      `₩${(value / 1000000).toFixed(0)}M`
                    }
                  />
                  <Tooltip
                    formatter={(value) => [
                      `₩${Number(value).toLocaleString()}`,
                      "자산",
                    ]}
                  />
                  <Line
                    type="monotone"
                    dataKey="value"
                    stroke="#2563eb"
                    strokeWidth={2}
                    dot={{ fill: "#2563eb" }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Profit Chart */}
        <Card>
          <CardHeader>
            <CardTitle>손익 현황</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey={xKey} />
                  <YAxis
                    tickFormatter={(value) =>
                      value >= 0 ? `+${(value / 10000).toFixed(0)}만` : `${(value / 10000).toFixed(0)}만`
                    }
                  />
                  <Tooltip
                    formatter={(value) => {
                      const num = Number(value);
                      return [`${num >= 0 ? "+" : ""}₩${num.toLocaleString()}`, "손익"];
                    }}
                  />
                  <Bar
                    dataKey="profit"
                    fill="#2563eb"
                    radius={[4, 4, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Trade Stats */}
      <Card>
        <CardHeader>
          <CardTitle>거래 통계</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={tradeStats} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis dataKey="name" type="category" />
                <Tooltip />
                <Bar dataKey="count" fill="#2563eb" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
