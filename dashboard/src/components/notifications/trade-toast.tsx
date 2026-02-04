"use client";

import { useEffect } from "react";
import { toast } from "sonner";
import { useTradesRealtime } from "@/hooks/use-realtime";

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

export function TradeNotifications() {
  useTradesRealtime({
    onNewTrade: (trade) => {
      const isBuy = trade.order_type === "buy";
      const icon = isBuy ? "📈" : "📉";
      const action = isBuy ? "매수" : "매도";
      const priceFormatted = trade.price.toLocaleString();
      const quantityFormatted = trade.quantity.toLocaleString();

      toast(`${icon} ${action} 주문`, {
        description: `${trade.stock_name} ${quantityFormatted}주 @ ₩${priceFormatted}`,
        duration: 5000,
      });
    },
    onTradeUpdate: ({ old: oldTrade, new: newTrade }) => {
      // Only notify when status changes to executed
      if (oldTrade.status !== "executed" && newTrade.status === "executed") {
        const isBuy = newTrade.order_type === "buy";
        const icon = isBuy ? "✅" : "💰";
        const action = isBuy ? "매수" : "매도";
        const priceFormatted = (newTrade.executed_price || newTrade.price).toLocaleString();
        const quantityFormatted = newTrade.executed_quantity.toLocaleString();

        toast.success(`${icon} ${action} 체결 완료`, {
          description: `${newTrade.stock_name} ${quantityFormatted}주 @ ₩${priceFormatted}`,
          duration: 5000,
        });
      }
    },
  });

  return null;
}

// Utility function to show trade notifications manually
export function showTradeNotification(trade: Trade, type: "new" | "executed") {
  const isBuy = trade.order_type === "buy";

  if (type === "new") {
    const icon = isBuy ? "📈" : "📉";
    const action = isBuy ? "매수" : "매도";
    toast(`${icon} ${action} 주문`, {
      description: `${trade.stock_name} ${trade.quantity.toLocaleString()}주`,
      duration: 5000,
    });
  } else {
    const icon = isBuy ? "✅" : "💰";
    const action = isBuy ? "매수" : "매도";
    toast.success(`${icon} ${action} 체결`, {
      description: `${trade.stock_name} ${trade.executed_quantity.toLocaleString()}주`,
      duration: 5000,
    });
  }
}
