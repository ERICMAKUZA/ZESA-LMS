'use client'

import Link from 'next/link'
import HeroCarousel from '@/components/landing/HeroCarousel'
import SearchBar from '@/components/landing/SearchBar'
import StatsStrip from '@/components/landing/StatsStrip'
import CategoryChips from '@/components/landing/CategoryChips'
import PopularCourses from '@/components/landing/PopularCourses'
import WhySection from '@/components/landing/WhySection'
import CTABanner from '@/components/landing/CTABanner'

export default function LandingPage() {
  return (
    <div className="min-h-screen flex flex-col bg-white">
      {/* sticky nav */}
      <header className="sticky top-0 z-50 border-b border-gray-100 bg-white/95 backdrop-blur-sm">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6">
          <Link href="/" className="flex flex-col leading-tight">
            <span className="text-lg font-extrabold text-primary tracking-tight">ZESA NTC</span>
            <span className="text-[10px] font-medium text-gray-400 tracking-wide uppercase">National Training Centre</span>
          </Link>
          <nav className="flex items-center gap-4 sm:gap-6">
            <Link href="/courses" className="hidden sm:block text-sm font-medium text-gray-600 hover:text-primary transition-colors">
              Courses
            </Link>
            <Link href="/login" className="text-sm font-medium text-gray-600 hover:text-primary transition-colors">
              Sign In
            </Link>
            <Link
              href="/login"
              className="rounded-lg border border-primary px-4 py-2 text-sm font-semibold text-primary hover:bg-primary hover:text-white transition-colors"
            >
              Get Started
            </Link>
          </nav>
        </div>
      </header>

      <main className="flex-1">
        {/* hero + overlapping search */}
        <div className="relative">
          <HeroCarousel />
          <SearchBar />
        </div>

        <StatsStrip />
        <CategoryChips />
        <PopularCourses />
        <WhySection />
        <CTABanner />
      </main>

      {/* footer */}
      <footer className="bg-primary-dark text-white/70 py-10">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <span className="text-base font-bold text-white">Training at ZESA National Training Centre</span>
          <p className="text-xs">© {new Date().getFullYear()} Zimbabwe Electricity Supply Authority. All rights reserved.</p>
          <nav className="flex gap-4 text-xs">
            <Link href="/courses" className="hover:text-white transition-colors">Courses</Link>
            <Link href="/login" className="hover:text-white transition-colors">Sign In</Link>
            <Link href="/register" className="hover:text-white transition-colors">Register</Link>
          </nav>
        </div>
      </footer>
    </div>
  )
}
