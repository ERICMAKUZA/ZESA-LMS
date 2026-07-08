const stats = [
  { value: '500+', label: 'Learners Trained' },
  { value: '12',   label: 'Certified Programmes' },
  { value: '98%',  label: 'Completion Rate' },
  { value: '24/7', label: 'Platform Access' },
]

export default function StatsStrip() {
  return (
    <section className="bg-white pt-16 pb-10 border-b border-gray-100">
      <div className="mx-auto max-w-7xl px-4 sm:px-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
          {stats.map(({ value, label }) => (
            <div key={label}>
              <p className="text-3xl font-bold text-primary">{value}</p>
              <p className="mt-1 text-sm text-gray-500">{label}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
