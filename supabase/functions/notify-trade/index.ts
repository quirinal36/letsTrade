// Supabase Edge Function: notify-trade
// Triggered when a trade is executed - sends notifications

import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { corsHeaders } from "../_shared/cors.ts";
import { getSupabaseClient } from "../_shared/supabase.ts";

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

interface WebhookPayload {
  type: "INSERT" | "UPDATE" | "DELETE";
  table: string;
  record: Trade;
  old_record: Trade | null;
  schema: string;
}

serve(async (req) => {
  // Handle CORS
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  try {
    const payload: WebhookPayload = await req.json();
    const { type, record, old_record } = payload;

    console.log(`Trade notification triggered: ${type}`, record);

    // Only process executed trades
    if (type === "UPDATE" && old_record?.status !== "executed" && record.status === "executed") {
      await sendTradeExecutedNotification(record);
    }

    // New trade order
    if (type === "INSERT") {
      await sendNewTradeNotification(record);
    }

    return new Response(
      JSON.stringify({ success: true, message: "Notification processed" }),
      {
        headers: { ...corsHeaders, "Content-Type": "application/json" },
        status: 200,
      }
    );
  } catch (error) {
    console.error("Error processing notification:", error);
    return new Response(
      JSON.stringify({ success: false, error: error.message }),
      {
        headers: { ...corsHeaders, "Content-Type": "application/json" },
        status: 500,
      }
    );
  }
});

async function sendNewTradeNotification(trade: Trade) {
  const action = trade.order_type === "buy" ? "매수" : "매도";
  const message = `[주문] ${trade.stock_name} ${action} ${trade.quantity}주 @ ₩${trade.price.toLocaleString()}`;

  console.log("New trade notification:", message);

  // Store notification in database for client to fetch
  const supabase = getSupabaseClient();
  await supabase.from("notifications").insert({
    type: "trade_new",
    title: `${action} 주문`,
    message,
    data: { trade_id: trade.id, stock_code: trade.stock_code },
    created_at: new Date().toISOString(),
  });

  // Send to external services (webhook, email, etc.) if configured
  await sendWebhookNotification("trade_new", message, trade);
}

async function sendTradeExecutedNotification(trade: Trade) {
  const action = trade.order_type === "buy" ? "매수" : "매도";
  const executedPrice = trade.executed_price || trade.price;
  const message = `[체결] ${trade.stock_name} ${action} ${trade.executed_quantity}주 @ ₩${executedPrice.toLocaleString()}`;

  console.log("Trade executed notification:", message);

  // Store notification in database
  const supabase = getSupabaseClient();
  await supabase.from("notifications").insert({
    type: "trade_executed",
    title: `${action} 체결 완료`,
    message,
    data: { trade_id: trade.id, stock_code: trade.stock_code },
    created_at: new Date().toISOString(),
  });

  // Send to external services
  await sendWebhookNotification("trade_executed", message, trade);
}

async function sendWebhookNotification(type: string, message: string, data: unknown) {
  const webhookUrl = Deno.env.get("NOTIFICATION_WEBHOOK_URL");

  if (!webhookUrl) {
    console.log("No webhook URL configured, skipping external notification");
    return;
  }

  try {
    const response = await fetch(webhookUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        type,
        message,
        data,
        timestamp: new Date().toISOString(),
      }),
    });

    if (!response.ok) {
      console.error("Webhook notification failed:", response.status);
    }
  } catch (error) {
    console.error("Error sending webhook notification:", error);
  }
}
