import { tool } from "ai";
import { z } from "zod";

const strategyInputSchema = z.object({
  name: z.string().describe("전략 이름"),
  description: z.string().describe("전략에 대한 설명"),
  strategy_type: z
    .enum(["ma_crossover", "rsi_oversold", "bollinger_bands", "macd", "custom"])
    .describe("전략 유형"),
  parameters: z
    .record(z.string(), z.unknown())
    .optional()
    .describe("전략별 파라미터 (예: { short_period: 5, long_period: 20 })"),
  stock_codes: z
    .string()
    .optional()
    .describe("대상 종목 코드, 콤마로 구분 (예: '005930,000660')"),
  max_investment: z
    .number()
    .optional()
    .describe("최대 투자금액 (원)"),
  max_loss_rate: z
    .number()
    .optional()
    .describe("손절선 (%, 양수로 입력. 예: 5는 -5% 손절)"),
  take_profit_rate: z
    .number()
    .optional()
    .describe("익절선 (%, 양수로 입력. 예: 10은 +10% 익절)"),
});

const modifyInputSchema = z.object({
  field: z.string().describe("수정할 필드명"),
  value: z.unknown().describe("새로운 값"),
});

export const strategyTools = {
  create_strategy: tool({
    description: "새로운 매매 전략을 생성합니다. 사용자가 전략을 만들고 싶다고 하면 이 도구를 사용하세요.",
    inputSchema: strategyInputSchema,
  }),

  modify_strategy: tool({
    description: "기존 전략을 수정합니다. 일부 파라미터만 변경할 때 사용하세요.",
    inputSchema: modifyInputSchema,
  }),
};

export type StrategyType = "ma_crossover" | "rsi_oversold" | "bollinger_bands" | "macd" | "custom";

export interface Strategy {
  name: string;
  description: string;
  strategy_type: StrategyType;
  parameters?: Record<string, unknown>;
  stock_codes?: string;
  max_investment?: number;
  max_loss_rate?: number;
  take_profit_rate?: number;
  is_active: boolean;
  priority: number;
}
