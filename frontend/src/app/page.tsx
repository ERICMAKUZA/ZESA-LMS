'use client'

import { useState } from 'react'
import Link from 'next/link'
import HeroCarousel from '@/components/landing/HeroCarousel'
import SearchBar from '@/components/landing/SearchBar'
import StatsStrip from '@/components/landing/StatsStrip'
import CategoryChips from '@/components/landing/CategoryChips'
import PopularCourses from '@/components/landing/PopularCourses'
import WhySection from '@/components/landing/WhySection'
import CTABanner from '@/components/landing/CTABanner'
import { FAQSection } from '@/components/FAQSection'
import EnquiryModal from '@/components/EnquiryModal'
import PublicNav from '@/components/layout/PublicNav'

export default function LandingPage() {
  const [enquiryOpen, setEnquiryOpen] = useState(false)

  return (
    <div className="min-h-screen flex flex-col bg-white">
      <PublicNav />

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
        <FAQSection onEnquire={() => setEnquiryOpen(true)} />
        <CTABanner onEnquire={() => setEnquiryOpen(true)} />
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

      <EnquiryModal open={enquiryOpen} onClose={() => setEnquiryOpen(false)} />
    </div>
  )
}
