import Image from 'next/image'
import { clsx } from 'clsx'

/**
 * The source file has a plain white background, so on dark navbars
 * (variant="dark") it needs a light chip behind it to avoid a harsh
 * white box; on light navbars it can sit directly on the page.
 */
export default function BrandLogo({
  variant = 'light',
  className,
}: {
  variant?: 'light' | 'dark'
  className?: string
}) {
  return (
    <span
      className={clsx(
        'inline-flex items-center',
        variant === 'dark' && 'rounded-md bg-white px-2 py-1',
        className,
      )}
    >
      <Image
        src="/logo.jpg"
        alt="ZESA National Training Centre"
        width={120}
        height={58}
        priority
        className="h-8 w-auto object-contain"
      />
    </span>
  )
}
