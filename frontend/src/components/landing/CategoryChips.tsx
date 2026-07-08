'use client'

import Image from 'next/image'
import Link from 'next/link'
import { useQuery } from '@tanstack/react-query'
import publicApi from '@/lib/publicApi'
import { getCategoryChipImage } from '@/lib/courseImages'
import type { CourseCategory } from '@/types'

// Skeleton shown while loading
function CategorySkeleton() {
  return (
    <div className="grid gap-6 grid-cols-2 sm:grid-cols-4">
      {Array.from({ length: 4 }).map((_, i) => (
        <div key={i} className="rounded-xl overflow-hidden border border-gray-100 animate-pulse">
          <div className="h-40 bg-gray-200" />
          <div className="p-4">
            <div className="h-4 bg-gray-200 rounded w-3/4" />
          </div>
        </div>
      ))}
    </div>
  )
}

export default function CategoryChips() {
  const { data: categories = [], isLoading } = useQuery<CourseCategory[]>({
    queryKey: ['categories'],
    queryFn: () => publicApi.get('/courses/categories/').then(r => r.data),
    staleTime: 5 * 60 * 1000,
  })

  return (
    <section className="py-12 bg-white">
      <div className="mx-auto max-w-7xl px-4 sm:px-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Browse by Category</h2>

        {isLoading ? (
          <CategorySkeleton />
        ) : (
          <div className="grid gap-6 grid-cols-2 sm:grid-cols-4">
            {categories.map(cat => (
              <Link
                key={cat.id}
                href={`/courses?category=${cat.id}`}
                className="group flex flex-col rounded-xl overflow-hidden border border-gray-100 bg-white hover:shadow-lg hover:-translate-y-1 transition-all duration-200"
              >
                <div className="relative h-40 w-full overflow-hidden">
                  <Image
                    src={getCategoryChipImage(cat.name)}
                    alt={cat.name}
                    fill
                    className="object-cover group-hover:scale-105 transition-transform duration-300"
                    sizes="(max-width: 640px) 50vw, 25vw"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent" />
                  {cat.course_count != null && (
                    <span className="absolute bottom-2 left-3 text-xs font-semibold text-white/80">
                      {cat.course_count} programme{cat.course_count !== 1 ? 's' : ''}
                    </span>
                  )}
                </div>
                <div className="p-4 flex-1 flex items-center">
                  <p className="text-sm font-bold text-gray-900 leading-snug">{cat.name}</p>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </section>
  )
}
