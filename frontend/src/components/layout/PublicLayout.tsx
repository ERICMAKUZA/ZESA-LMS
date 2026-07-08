import type { ReactNode } from 'react'
import PublicNav from './PublicNav'

export default function PublicLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <PublicNav />
      <main className="flex-1 p-6">{children}</main>
    </div>
  )
}
