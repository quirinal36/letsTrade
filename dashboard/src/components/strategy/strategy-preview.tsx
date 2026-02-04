"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { STRATEGY_TYPE_LABELS } from "@/lib/ai/strategy-prompts";
import type { Strategy } from "@/lib/ai/strategy-tools";

interface StrategyPreviewProps {
  strategy: Strategy | null;
  onSave: () => void;
  onClear: () => void;
  isSaving: boolean;
}

export function StrategyPreview({ strategy, onSave, onClear, isSaving }: StrategyPreviewProps) {
  if (!strategy) {
    return (
      <Card className="h-full">
        <CardHeader>
          <CardTitle className="text-lg">전략 미리보기</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-12 text-center text-gray-500">
            <p>AI와 대화하여 전략을 생성하세요</p>
            <p className="mt-2 text-sm">
              예: &quot;RSI가 30 이하일 때 매수하는 전략 만들어줘&quot;
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="h-full">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">전략 미리보기</CardTitle>
          <Badge variant="outline">
            {STRATEGY_TYPE_LABELS[strategy.strategy_type] || strategy.strategy_type}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <h3 className="font-semibold text-lg">{strategy.name}</h3>
          <p className="text-sm text-gray-500 mt-1">{strategy.description}</p>
        </div>

        {strategy.parameters && Object.keys(strategy.parameters).length > 0 && (
          <div>
            <p className="text-sm font-medium text-gray-500 mb-2">파라미터</p>
            <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3">
              <div className="grid grid-cols-2 gap-2 text-sm">
                {Object.entries(strategy.parameters).map(([key, value]) => (
                  <div key={key}>
                    <span className="text-gray-500">{key}:</span>{" "}
                    <span className="font-medium">{String(value)}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {strategy.stock_codes && (
          <div>
            <p className="text-sm font-medium text-gray-500 mb-1">대상 종목</p>
            <p className="text-sm">{strategy.stock_codes}</p>
          </div>
        )}

        {strategy.max_investment && (
          <div>
            <p className="text-sm font-medium text-gray-500 mb-1">최대 투자금</p>
            <p className="text-sm font-medium">
              {strategy.max_investment.toLocaleString()}원
            </p>
          </div>
        )}

        <div className="grid grid-cols-2 gap-3">
          <div className="p-3 bg-red-50 dark:bg-red-950 rounded-lg">
            <p className="text-sm text-red-600">손절선</p>
            <p className="text-xl font-bold text-red-600">
              {strategy.max_loss_rate ? `-${strategy.max_loss_rate}%` : "미설정"}
            </p>
          </div>
          <div className="p-3 bg-green-50 dark:bg-green-950 rounded-lg">
            <p className="text-sm text-green-600">익절선</p>
            <p className="text-xl font-bold text-green-600">
              {strategy.take_profit_rate ? `+${strategy.take_profit_rate}%` : "미설정"}
            </p>
          </div>
        </div>

        <div className="flex gap-2 pt-2">
          <Button onClick={onSave} disabled={isSaving} className="flex-1">
            {isSaving ? "저장 중..." : "전략 저장"}
          </Button>
          <Button variant="outline" onClick={onClear}>
            초기화
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
