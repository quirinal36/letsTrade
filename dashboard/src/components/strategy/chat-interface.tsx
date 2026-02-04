"use client";

import { useChat } from "@ai-sdk/react";
import { DefaultChatTransport } from "ai";
import { useEffect, useRef, useState, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Send, Bot, User, Sparkles } from "lucide-react";
import type { Strategy } from "@/lib/ai/strategy-tools";

interface ChatInterfaceProps {
  onStrategyGenerated: (strategy: Strategy) => void;
}

const EXAMPLE_PROMPTS = [
  "RSI가 30 이하일 때 매수하는 전략",
  "5일선이 20일선을 상향 돌파하면 매수",
  "볼린저밴드 하단 터치 시 매수",
  "삼성전자에 100만원 한도로 투자하는 MACD 전략",
];

export function ChatInterface({ onStrategyGenerated }: ChatInterfaceProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [input, setInput] = useState("");
  const [hasInteracted, setHasInteracted] = useState(false);

  const transport = useMemo(
    () => new DefaultChatTransport({ api: "/api/chat/strategy" }),
    []
  );

  const { messages, sendMessage, status } = useChat({
    transport,
  });

  const isLoading = status === "streaming" || status === "submitted";

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    // Check for tool calls in messages
    for (const message of messages) {
      if (message.role === "assistant" && message.parts) {
        for (const part of message.parts) {
          // Check if it's a tool part with create_strategy
          if (part.type?.startsWith("tool-") && "toolCallId" in part) {
            const toolPart = part as { type: string; toolCallId: string; state: string; input?: unknown };
            if (toolPart.type === "tool-create_strategy" && toolPart.input) {
              const args = toolPart.input as Strategy;
              onStrategyGenerated({
                ...args,
                is_active: false,
                priority: 0,
              });
            }
          }
        }
      }
    }
  }, [messages, onStrategyGenerated]);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    setHasInteracted(true);
    const messageToSend = input;
    setInput("");

    await sendMessage({ text: messageToSend });
  };

  const handleExampleClick = async (prompt: string) => {
    if (isLoading) return;

    setHasInteracted(true);
    await sendMessage({ text: prompt });
  };

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="pb-3">
        <CardTitle className="text-lg flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-purple-500" />
          AI 전략 어시스턴트
        </CardTitle>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col overflow-hidden">
        <div className="flex-1 overflow-y-auto space-y-4 mb-4">
          {!hasInteracted && messages.length === 0 && (
            <div className="space-y-4">
              <div className="flex gap-3">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-purple-100 dark:bg-purple-900 flex items-center justify-center">
                  <Bot className="h-4 w-4 text-purple-600" />
                </div>
                <div className="flex-1 bg-gray-100 dark:bg-gray-800 rounded-lg p-3">
                  <p>안녕하세요! 어떤 매매 전략을 만들고 싶으신가요?</p>
                  <p className="text-sm text-gray-500 mt-2">
                    자연어로 원하는 전략을 설명해 주시면 자동으로 구조화된 전략을 생성해 드립니다.
                  </p>
                </div>
              </div>

              <div className="pl-11">
                <p className="text-sm text-gray-500 mb-2">예시를 클릭해 보세요:</p>
                <div className="flex flex-wrap gap-2">
                  {EXAMPLE_PROMPTS.map((prompt, index) => (
                    <button
                      key={index}
                      onClick={() => handleExampleClick(prompt)}
                      className="text-sm px-3 py-1.5 bg-purple-50 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded-full hover:bg-purple-100 dark:hover:bg-purple-900/50 transition-colors"
                    >
                      {prompt}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {messages.map((message) => {
            // Extract text content from message parts
            const textContent = message.parts
              .filter((part): part is { type: "text"; text: string } => part.type === "text")
              .map((part) => part.text)
              .join("");

            if (!textContent) return null;

            return (
              <div key={message.id} className="flex gap-3">
                <div
                  className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                    message.role === "user"
                      ? "bg-blue-100 dark:bg-blue-900"
                      : "bg-purple-100 dark:bg-purple-900"
                  }`}
                >
                  {message.role === "user" ? (
                    <User className="h-4 w-4 text-blue-600" />
                  ) : (
                    <Bot className="h-4 w-4 text-purple-600" />
                  )}
                </div>
                <div
                  className={`flex-1 rounded-lg p-3 ${
                    message.role === "user"
                      ? "bg-blue-50 dark:bg-blue-900/30"
                      : "bg-gray-100 dark:bg-gray-800"
                  }`}
                >
                  <p className="whitespace-pre-wrap">{textContent}</p>
                </div>
              </div>
            );
          })}

          {isLoading && (
            <div className="flex gap-3">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-purple-100 dark:bg-purple-900 flex items-center justify-center">
                <Bot className="h-4 w-4 text-purple-600" />
              </div>
              <div className="flex-1 bg-gray-100 dark:bg-gray-800 rounded-lg p-3">
                <div className="flex items-center gap-2">
                  <div className="animate-pulse flex gap-1">
                    <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: "0ms" }}></div>
                    <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: "150ms" }}></div>
                    <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: "300ms" }}></div>
                  </div>
                  <span className="text-sm text-gray-500">전략을 생성하고 있어요...</span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <form onSubmit={handleSubmit} className="flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="전략을 설명해 주세요..."
            disabled={isLoading}
            className="flex-1"
          />
          <Button type="submit" disabled={isLoading || !input.trim()}>
            <Send className="h-4 w-4" />
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
