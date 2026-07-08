import Link from 'next/link'

interface Props {
  onEnquire?: () => void
}

export default function CTABanner({ onEnquire }: Props) {
  return (
    <section className="bg-gradient-to-r from-primary to-primary-dark py-16">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 text-center">
        <p className="text-sm font-semibold tracking-widest uppercase text-accent mb-3">
          Empowering Zimbabwe's Future Through Excellence
        </p>
        <h2 className="text-3xl md:text-4xl font-bold text-white">
          Ready to advance your career?
        </h2>
        <p className="mt-3 text-white/80 text-base md:text-lg max-w-xl mx-auto">
          Join hundreds of professionals and apprentices already building skills at the National Training Centre.
        </p>
        <div className="mt-8 flex flex-wrap items-center justify-center gap-4">
          <Link
            href="/register"
            className="rounded-lg bg-accent hover:bg-accent-light text-primary-dark font-semibold px-8 py-3 text-base transition-colors"
          >
            Get Started
          </Link>
          {onEnquire && (
            <button
              onClick={onEnquire}
              className="rounded-lg border-2 border-white/60 hover:border-white text-white font-semibold px-8 py-3 text-base transition-colors hover:bg-white/10"
            >
              Make an Enquiry
            </button>
          )}
        </div>
      </div>
    </section>
  )
}
