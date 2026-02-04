// Supabase Edge Function: notify-alert
// Triggered for urgent alerts (stop-loss, large price movements, etc.)

import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { corsHeaders } from "../_shared/cors.ts";
import { getSupabaseClient } from "../_shared/supabase.ts";

interface AlertRequest {
  type: "stop_loss" | "take_profit" | "price_alert" | "system_error";
  stock_code?: string;
  stock_name?: string;
  message: string;
  severity: "info" | "warning" | "critical";
  data?: Record<string, unknown>;
}

serve(async (req) => {
  // Handle CORS
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  try {
    const alert: AlertRequest = await req.json();

    console.log(`Alert notification triggered: ${alert.type}`, alert);

    // Validate required fields
    if (!alert.type || !alert.message) {
      return new Response(
        JSON.stringify({ success: false, error: "Missing required fields: type, message" }),
        {
          headers: { ...corsHeaders, "Content-Type": "application/json" },
          status: 400,
        }
      );
    }

    // Process alert based on type
    await processAlert(alert);

    return new Response(
      JSON.stringify({ success: true, message: "Alert processed" }),
      {
        headers: { ...corsHeaders, "Content-Type": "application/json" },
        status: 200,
      }
    );
  } catch (error) {
    console.error("Error processing alert:", error);
    return new Response(
      JSON.stringify({ success: false, error: error.message }),
      {
        headers: { ...corsHeaders, "Content-Type": "application/json" },
        status: 500,
      }
    );
  }
});

async function processAlert(alert: AlertRequest) {
  const supabase = getSupabaseClient();

  // Determine title based on type
  const titles: Record<string, string> = {
    stop_loss: "손절선 도달",
    take_profit: "익절선 도달",
    price_alert: "가격 알림",
    system_error: "시스템 오류",
  };

  const title = titles[alert.type] || "알림";

  // Store notification in database
  await supabase.from("notifications").insert({
    type: alert.type,
    title,
    message: alert.message,
    severity: alert.severity,
    data: {
      stock_code: alert.stock_code,
      stock_name: alert.stock_name,
      ...alert.data,
    },
    created_at: new Date().toISOString(),
  });

  // For critical alerts, send to external services immediately
  if (alert.severity === "critical") {
    await sendUrgentNotification(alert);
  }

  // Send webhook notification
  await sendWebhookNotification(alert);
}

async function sendUrgentNotification(alert: AlertRequest) {
  console.log("URGENT ALERT:", alert.message);

  // Send email notification if configured
  const emailApiKey = Deno.env.get("EMAIL_API_KEY");
  const emailTo = Deno.env.get("ALERT_EMAIL");

  if (emailApiKey && emailTo) {
    // Example: Send via SendGrid or similar service
    // This is a placeholder - implement based on your email provider
    console.log(`Would send email to ${emailTo}: ${alert.message}`);
  }

  // Send SMS notification if configured
  const smsApiKey = Deno.env.get("SMS_API_KEY");
  const smsTo = Deno.env.get("ALERT_PHONE");

  if (smsApiKey && smsTo) {
    // Example: Send via Twilio or similar service
    // This is a placeholder - implement based on your SMS provider
    console.log(`Would send SMS to ${smsTo}: ${alert.message}`);
  }
}

async function sendWebhookNotification(alert: AlertRequest) {
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
        type: `alert_${alert.type}`,
        message: alert.message,
        severity: alert.severity,
        data: {
          stock_code: alert.stock_code,
          stock_name: alert.stock_name,
          ...alert.data,
        },
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

// Helper function to check portfolio for stop-loss conditions
export async function checkStopLossConditions() {
  const supabase = getSupabaseClient();

  // Get all positions with their strategies
  const { data: positions, error } = await supabase
    .from("portfolio")
    .select("*, strategies!inner(max_loss_rate)")
    .lt("profit_loss_rate", 0);

  if (error) {
    console.error("Error fetching positions:", error);
    return;
  }

  for (const position of positions || []) {
    const maxLossRate = position.strategies?.max_loss_rate || 10;
    const currentLossRate = Math.abs(position.profit_loss_rate);

    if (currentLossRate >= maxLossRate) {
      await processAlert({
        type: "stop_loss",
        stock_code: position.stock_code,
        stock_name: position.stock_name,
        message: `${position.stock_name} 손절선(${maxLossRate}%) 도달! 현재 손실률: ${currentLossRate.toFixed(2)}%`,
        severity: "critical",
        data: {
          position_id: position.id,
          current_loss_rate: currentLossRate,
          max_loss_rate: maxLossRate,
        },
      });
    }
  }
}
