'use client'

import { useState } from 'react'
import Link from 'next/link'
import { formatDistanceToNow } from 'date-fns'
import { Bell, CheckCheck } from 'lucide-react'
import { clsx } from 'clsx'
import {
  useMarkAllNotificationsRead,
  useMarkNotificationRead,
  useNotifications,
  useUnreadNotificationCount,
} from '@/hooks/useNotifications'

export default function NotificationBell() {
  const [open, setOpen] = useState(false)
  const { data } = useNotifications()
  const { data: unread } = useUnreadNotificationCount()
  const markRead = useMarkNotificationRead()
  const markAllRead = useMarkAllNotificationsRead()
  const notifications = data?.results ?? []
  const unreadCount = unread?.count ?? 0

  const openNotification = (id: number) => {
    markRead.mutate(id)
    setOpen(false)
  }

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen((current) => !current)}
        className="relative rounded-full p-2 text-gray-500 hover:bg-gray-100 hover:text-primary"
        aria-label="Notifications"
      >
        <Bell className="h-5 w-5" />
        {unreadCount > 0 && (
          <span className="absolute -right-0.5 -top-0.5 min-w-5 rounded-full bg-red-600 px-1.5 py-0.5 text-center text-[10px] font-bold leading-none text-white">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 z-50 mt-2 w-96 max-w-[calc(100vw-2rem)] overflow-hidden rounded-xl border border-gray-200 bg-white shadow-xl">
          <div className="flex items-center justify-between border-b border-gray-100 px-4 py-3">
            <div>
              <p className="text-sm font-semibold text-gray-900">Notifications</p>
              <p className="text-xs text-gray-500">{unreadCount} unread</p>
            </div>
            <button
              type="button"
              onClick={() => markAllRead.mutate()}
              disabled={unreadCount === 0 || markAllRead.isPending}
              className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-semibold text-primary hover:bg-primary/10 disabled:text-gray-400"
            >
              <CheckCheck className="h-3.5 w-3.5" />
              Mark all read
            </button>
          </div>

          <div className="max-h-96 overflow-y-auto">
            {notifications.length === 0 ? (
              <p className="px-4 py-8 text-center text-sm text-gray-500">
                No notifications yet.
              </p>
            ) : (
              notifications.slice(0, 10).map((item) => {
                const content = (
                  <div
                    className={clsx(
                      'border-b border-gray-100 px-4 py-3 text-left hover:bg-gray-50',
                      !item.is_read && 'bg-blue-50/60',
                    )}
                  >
                    <div className="flex gap-3">
                      <span
                        className={clsx(
                          'mt-1 h-2 w-2 shrink-0 rounded-full',
                          item.is_read ? 'bg-gray-300' : 'bg-primary',
                        )}
                      />
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-semibold text-gray-900">{item.subject}</p>
                        <p className="mt-1 line-clamp-2 text-xs text-gray-600">{item.message}</p>
                        <p className="mt-2 text-[11px] text-gray-400">
                          {formatDistanceToNow(new Date(item.created_at), { addSuffix: true })}
                        </p>
                      </div>
                    </div>
                  </div>
                )

                if (item.action_url) {
                  return (
                    <Link
                      key={item.id}
                      href={item.action_url}
                      onClick={() => openNotification(item.id)}
                      className="block"
                    >
                      {content}
                    </Link>
                  )
                }

                return (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => openNotification(item.id)}
                    className="block w-full"
                  >
                    {content}
                  </button>
                )
              })
            )}
          </div>
        </div>
      )}
    </div>
  )
}
