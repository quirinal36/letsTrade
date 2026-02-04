import { anthropic } from "@ai-sdk/anthropic";
import { streamText } from "ai";
import { STRATEGY_SYSTEM_PROMPT } from "@/lib/ai/strategy-prompts";
import { strategyTools } from "@/lib/ai/strategy-tools";

export const maxDuration = 30;

export async function POST(req: Request) {
  const { messages } = await req.json();

  const result = streamText({
    model: anthropic("claude-sonnet-4-20250514"),
    system: STRATEGY_SYSTEM_PROMPT,
    messages,
    tools: strategyTools,
  });

  return result.toTextStreamResponse();
}
