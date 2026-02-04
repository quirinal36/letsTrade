"use client";

import { useState } from "react";
import { useNotifications, type Notification } from "@/hooks/use-notifications";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { format } from "date-fns";
import { ko } from "date-fns/locale";

export function NotificationBell() {
  const { notifications, unreadCount, markAsRead, markAllAsRead } = useNotifications();
  const [isOpen, setIsOpen] = useState(false);

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case "critical":
        return "bg-red-500";
      case "warning":
        return "bg-yellow-500";
      default:
        return "bg-blue-500";
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case "trade_new":
        return "📝";
      case "trade_executed":
        return "✅";
      case "stop_loss":
        return "🔴";
      case "take_profit":
        return "🟢";
      case "price_alert":
        return "📊";
      case "system_error":
        return "⚠️";
      default:
        return "🔔";
    }
  };

  return (
    <div className="relative">
      <Button
        variant="ghost"
        size="sm"
        className="relative"
        onClick={() => setIsOpen(!isOpen)}
      >
        <span className="text-xl">🔔</span>
        {unreadCount > 0 && (
          <Badge
            className="absolute -top-1 -right-1 h-5 w-5 rounded-full p-0 flex items-center justify-center text-xs"
            variant="destructive"
          >
            {unreadCount > 9 ? "9+" : unreadCount}
          </Badge>
        )}
      </Button>

      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />

          {/* Dropdown */}
          <Card className="absolute right-0 top-full mt-2 w-80 z-50 shadow-lg max-h-96 overflow-hidden">
            <CardHeader className="py-3 px-4 border-b flex flex-row items-center justify-between">
              <CardTitle className="text-sm font-medium">알림</CardTitle>
              {unreadCount > 0 && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-xs h-auto py-1"
                  onClick={markAllAsRead}
                >
                  모두 읽음
                </Button>
              )}
            </CardHeader>
            <CardContent className="p-0 max-h-72 overflow-y-auto">
              {notifications.length === 0 ? (
                <p className="text-sm text-gray-500 text-center py-8">
                  알림이 없습니다
                </p>
              ) : (
                <div className="divide-y">
                  {notifications.slice(0, 10).map((notification) => (
                    <NotificationItem
                      key={notification.id}
                      notification={notification}
                      onRead={markAsRead}
                    />
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}

function NotificationItem({
  notification,
  onRead,
}: {
  notification: Notification;
  onRead: (id: number) => void;
}) {
  const getTypeIcon = (type: string) => {
    switch (type) {
      case "trade_new":
        return "📝";
      case "trade_executed":
        return "✅";
      case "stop_loss":
        return "🔴";
      case "take_profit":
        return "🟢";
      case "price_alert":
        return "📊";
      case "system_error":
        return "⚠️";
      default:
        return "🔔";
    }
  };

  const handleClick = () => {
    if (!notification.is_read) {
      onRead(notification.id);
    }
  };

  return (
    <div
      className={`p-3 hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer transition-colors ${
        !notification.is_read ? "bg-blue-50/50 dark:bg-blue-900/20" : ""
      }`}
      onClick={handleClick}
    >
      <div className="flex items-start gap-3">
        <span className="text-lg mt-0.5">{getTypeIcon(notification.type)}</span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <p className="text-sm font-medium truncate">{notification.title}</p>
            {!notification.is_read && (
              <span className="w-2 h-2 rounded-full bg-blue-500 flex-shrink-0" />
            )}
          </div>
          <p className="text-xs text-gray-500 line-clamp-2 mt-0.5">
            {notification.message}
          </p>
          <p className="text-xs text-gray-400 mt-1">
            {format(new Date(notification.created_at), "MM/dd HH:mm", { locale: ko })}
          </p>
        </div>
        {notification.severity === "critical" && (
          <Badge variant="destructive" className="flex-shrink-0 text-xs">
            긴급
          </Badge>
        )}
      </div>
    </div>
  );
}
