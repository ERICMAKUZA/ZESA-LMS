import Link from 'next/link'

export default function CTABanner() {
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
          Join hundreds of ZESA employees already building skills at the National Training Centre.
        </p>
        <Link
          href="/login"
          className="mt-8 inline-block rounded-lg bg-accent hover:bg-accent-light text-primary-dark font-semibold px-8 py-3 text-base transition-colors"
        >
          Get Started
        </Link>
      </div>
    </section>
  )
}
