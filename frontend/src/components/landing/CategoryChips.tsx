'use client'

import Image from 'next/image'
import Link from 'next/link'

const categories = [
  {
    name: 'Drone Technology',
    slug: 'drone-technology',
    courses: 1,
    image: 'https://images.unsplash.com/photo-1473968512647-3e447244af8f?auto=format&fit=crop&w=400&q=70',
  },
  {
    name: 'Renewable Energy',
    slug: 'renewable-energy',
    courses: 2,
    image: 'https://images.unsplash.com/photo-1509391366360-2e959784a276?auto=format&fit=crop&w=400&q=70',
  },
  {
    name: 'Technical Skills',
    slug: 'technical-skills',
    courses: 1,
    image: 'https://images.unsplash.com/photo-1581092160562-40aa08e78837?auto=format&fit=crop&w=400&q=70',
  },
  {
    name: 'Leadership',
    slug: 'leadership',
    courses: 1,
    image: 'https://images.unsplash.com/photo-1556761175-5973dc0f32e7?auto=format&fit=crop&w=400&q=70',
  },
]

export default function CategoryChips() {
  return (
    <section className="py-12 bg-white">
      <div className="mx-auto max-w-7xl px-4 sm:px-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Browse by Category</h2>
        <div className="flex gap-4 overflow-x-auto pb-2 scrollbar-hide">
          {categories.map((cat) => (
            <Link
              key={cat.slug}
              href={`/courses?category=${cat.slug}`}
              className="group flex-shrink-0 w-48 rounded-xl overflow-hidden border border-gray-100 hover:shadow-lg hover:-translate-y-1 transition-all duration-200"
            >
              <div className="relative h-28 w-full">
                <Image
                  src={cat.image}
                  alt={cat.name}
                  fill
                  className="object-cover group-hover:scale-105 transition-transform duration-300"
                  sizes="192px"
                />
              </div>
              <div className="p-3 bg-white">
                <p className="text-sm font-semibold text-gray-900 leading-snug">{cat.name}</p>
                <p className="text-xs text-gray-500 mt-0.5">{cat.courses} course{cat.courses !== 1 ? 's' : ''}</p>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </section>
  )
}
