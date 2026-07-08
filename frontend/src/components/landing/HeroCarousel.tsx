'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import Image from 'next/image'
import Link from 'next/link'
import { ChevronLeft, ChevronRight } from 'lucide-react'

const slides = [
  {
    image: 'https://images.unsplash.com/photo-1705579608642-19a05c1b7b96?auto=format&fit=crop&w=1920&q=80',
    heading: 'Advance Your Career at ZNTC',
    subtext: 'Certified programmes open to ZESA staff, apprentices, and self-funded applicants — from technical skills to leadership.',
  },
  {
    image: 'https://images.unsplash.com/photo-1531482615713-2afd69097998?auto=format&fit=crop&w=1920&q=80',
    heading: 'Learn From Industry Experts',
    subtext: 'Structured learning paths designed and reviewed by Zimbabwe\'s leading energy sector professionals.',
  },
  {
    image: 'https://plus.unsplash.com/premium_photo-1704756437789-8b033df16181?auto=format&fit=crop&w=1920&q=80',
    heading: 'Built for Zimbabwe\'s Energy Sector',
    subtext: 'Programmes aligned to HEXCO standards, designed around real-world operations, safety, and systems.',
  },
]

export default function HeroCarousel() {
  const [active, setActive] = useState(0)
  const [paused, setPaused] = useState(false)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const advance = useCallback((dir: 1 | -1) => {
    setActive((prev) => (prev + dir + slides.length) % slides.length)
  }, [])

  useEffect(() => {
    if (paused) return
    timerRef.current = setInterval(() => advance(1), 5000)
    return () => { if (timerRef.current) clearInterval(timerRef.current) }
  }, [paused, advance])

  return (
    <div
      className="group relative h-[420px] md:h-[560px] w-full overflow-hidden"
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
    >
      {slides.map((slide, i) => (
        <div
          key={i}
          className="absolute inset-0 transition-opacity duration-700"
          style={{ opacity: i === active ? 1 : 0, zIndex: i === active ? 1 : 0 }}
          aria-hidden={i !== active}
        >
          <Image
            src={slide.image}
            alt={slide.heading}
            fill
            className="object-cover"
            priority={i === 0}
            sizes="100vw"
          />
          {/* dark gradient overlay */}
          <div className="absolute inset-0 bg-gradient-to-t from-primary-dark/90 via-primary-dark/40 to-transparent" />
          {/* text content */}
          <div className="absolute inset-0 flex flex-col justify-end pb-20 md:pb-28 px-6 md:px-16 max-w-5xl">
            <h1 className="text-3xl md:text-5xl font-bold text-white leading-tight drop-shadow-sm">
              {slide.heading}
            </h1>
            <p className="mt-3 text-base md:text-lg text-white/90 max-w-xl drop-shadow-sm">
              {slide.subtext}
            </p>
            <Link
              href="/courses"
              className="mt-6 inline-flex w-fit items-center rounded-lg bg-accent hover:bg-accent-light text-primary-dark font-semibold px-6 py-3 text-sm md:text-base transition-colors"
            >
              Browse Courses
            </Link>
          </div>
        </div>
      ))}

      {/* prev/next arrows */}
      <button
        onClick={() => advance(-1)}
        className="absolute left-4 top-1/2 z-10 -translate-y-1/2 flex h-10 w-10 items-center justify-center rounded-full bg-white/20 text-white backdrop-blur-sm opacity-0 group-hover:opacity-100 transition-opacity hover:bg-white/40"
        aria-label="Previous slide"
      >
        <ChevronLeft className="h-5 w-5" />
      </button>
      <button
        onClick={() => advance(1)}
        className="absolute right-4 top-1/2 z-10 -translate-y-1/2 flex h-10 w-10 items-center justify-center rounded-full bg-white/20 text-white backdrop-blur-sm opacity-0 group-hover:opacity-100 transition-opacity hover:bg-white/40"
        aria-label="Next slide"
      >
        <ChevronRight className="h-5 w-5" />
      </button>

      {/* dot indicators */}
      <div className="absolute bottom-6 left-1/2 z-10 -translate-x-1/2 flex gap-2">
        {slides.map((_, i) => (
          <button
            key={i}
            onClick={() => setActive(i)}
            className={`h-2 w-2 rounded-full transition-all duration-300 ${
              i === active ? 'bg-accent w-6' : 'bg-white/50 hover:bg-white/80'
            }`}
            aria-label={`Go to slide ${i + 1}`}
          />
        ))}
      </div>
    </div>
  )
}
