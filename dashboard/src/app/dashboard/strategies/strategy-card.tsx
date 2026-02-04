"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";

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
}

interface StrategyCardProps {
  strategy: Strategy;
  signalCount: number;
}

export function StrategyCard({ strategy, signalCount }: StrategyCardProps) {
  const [isActive, setIsActive] = useState(strategy.is_active);
  const [isUpdating, setIsUpdating] = useState(false);
  const router = useRouter();

  const handleToggle = async () => {
    setIsUpdating(true);
    const newStatus = !isActive;

    const supabase = createClient();
    const { error } = await supabase
      .from("strategies")
      .update({ is_active: newStatus })
      .eq("id", strategy.id);

    if (!error) {
      setIsActive(newStatus);
    }
    setIsUpdating(false);
    router.refresh();
  };

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

  const stockList = strategy.stock_codes
    ? strategy.stock_codes.split(",").slice(0, 3)
    : [];

  return (
    <Card className={!isActive ? "opacity-60" : ""}>
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="text-lg">{strategy.name}</CardTitle>
            <Badge variant="outline" className="mt-1">
              {getTypeLabel(strategy.strategy_type)}
            </Badge>
          </div>
          <Switch
            checked={isActive}
            onCheckedChange={handleToggle}
            disabled={isUpdating}
          />
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {strategy.description && (
          <p className="text-sm text-gray-500 line-clamp-2">
            {strategy.description}
          </p>
        )}

        <div className="flex flex-wrap gap-1">
          {stockList.map((code) => (
            <Badge key={code} variant="secondary" className="text-xs">
              {code.trim()}
            </Badge>
          ))}
          {strategy.stock_codes &&
            strategy.stock_codes.split(",").length > 3 && (
              <Badge variant="secondary" className="text-xs">
                +{strategy.stock_codes.split(",").length - 3}
              </Badge>
            )}
        </div>

        <div className="grid grid-cols-2 gap-2 text-sm">
          <div>
            <p className="text-gray-500">최대 투자</p>
            <p className="font-medium">
              {strategy.max_investment
                ? `₩${strategy.max_investment.toLocaleString()}`
                : "-"}
            </p>
          </div>
          <div>
            <p className="text-gray-500">7일 시그널</p>
            <p className="font-medium">{signalCount}건</p>
          </div>
          <div>
            <p className="text-gray-500">손절선</p>
            <p className="font-medium text-red-600">
              {strategy.max_loss_rate ? `-${strategy.max_loss_rate}%` : "-"}
            </p>
          </div>
          <div>
            <p className="text-gray-500">익절선</p>
            <p className="font-medium text-green-600">
              {strategy.take_profit_rate
                ? `+${strategy.take_profit_rate}%`
                : "-"}
            </p>
          </div>
        </div>

        <div className="flex gap-2 pt-2">
          <Button
            variant="outline"
            size="sm"
            className="flex-1"
            onClick={() =>
              router.push(`/dashboard/strategies/${strategy.id}`)
            }
          >
            상세보기
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="flex-1"
            onClick={() =>
              router.push(`/dashboard/strategies/${strategy.id}/backtest`)
            }
          >
            백테스트
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
