"use client";

import { useEffect, useCallback, useRef } from "react";
import { createClient } from "@/lib/supabase/client";
import type { RealtimeChannel, RealtimePostgresChangesPayload } from "@supabase/supabase-js";

type PostgresChangeEvent = "INSERT" | "UPDATE" | "DELETE" | "*";

interface UseRealtimeOptions<T extends { [key: string]: unknown }> {
  table: string;
  event?: PostgresChangeEvent;
  filter?: string;
  onInsert?: (payload: T) => void;
  onUpdate?: (payload: { old: T; new: T }) => void;
  onDelete?: (payload: T) => void;
  onChange?: (payload: RealtimePostgresChangesPayload<T>) => void;
}

export function useRealtime<T extends { [key: string]: unknown }>({
  table,
  event = "*",
  filter,
  onInsert,
  onUpdate,
  onDelete,
  onChange,
}: UseRealtimeOptions<T>) {
  const channelRef = useRef<RealtimeChannel | null>(null);

  const handleChange = useCallback(
    (payload: RealtimePostgresChangesPayload<T>) => {
      onChange?.(payload);

      switch (payload.eventType) {
        case "INSERT":
          onInsert?.(payload.new as T);
          break;
        case "UPDATE":
          onUpdate?.({ old: payload.old as T, new: payload.new as T });
          break;
        case "DELETE":
          onDelete?.(payload.old as T);
          break;
      }
    },
    [onChange, onInsert, onUpdate, onDelete]
  );

  useEffect(() => {
    const supabase = createClient();

    const channelConfig: {
      event: PostgresChangeEvent;
      schema: string;
      table: string;
      filter?: string;
    } = {
      event,
      schema: "public",
      table,
    };

    if (filter) {
      channelConfig.filter = filter;
    }

    const channel = supabase
      .channel(`realtime:${table}`)
      .on(
        "postgres_changes",
        channelConfig,
        handleChange
      )
      .subscribe();

    channelRef.current = channel;

    return () => {
      if (channelRef.current) {
        supabase.removeChannel(channelRef.current);
      }
    };
  }, [table, event, filter, handleChange]);

  return channelRef.current;
}

// Hook for subscribing to trades
export function useTradesRealtime(callbacks: {
  onNewTrade?: (trade: Trade) => void;
  onTradeUpdate?: (trade: { old: Trade; new: Trade }) => void;
}) {
  return useRealtime<Trade>({
    table: "trades",
    onInsert: callbacks.onNewTrade,
    onUpdate: callbacks.onTradeUpdate,
  });
}

// Hook for subscribing to portfolio changes
export function usePortfolioRealtime(callbacks: {
  onPortfolioChange?: (position: Position) => void;
  onPositionUpdate?: (update: { old: Position; new: Position }) => void;
}) {
  return useRealtime<Position>({
    table: "portfolio",
    onInsert: callbacks.onPortfolioChange,
    onUpdate: callbacks.onPositionUpdate,
  });
}

// Types
interface Trade {
  [key: string]: unknown;
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

interface Position {
  [key: string]: unknown;
  id: number;
  stock_code: string;
  stock_name: string;
  quantity: number;
  avg_price: number;
  current_price: number;
  total_cost: number;
  market_value: number;
  profit_loss: number;
  profit_loss_rate: number;
}
