import { Clock, Award, Users } from 'lucide-react'

const features = [
  {
    icon: Clock,
    title: 'Flexible Learning',
    desc: 'Learn at your own pace, on any device, anytime.',
  },
  {
    icon: Award,
    title: 'Industry-Recognized Certificates',
    desc: 'Earn certificates verified with QR codes and digital signatures.',
  },
  {
    icon: Users,
    title: 'Expert-Led Content',
    desc: 'Courses built and reviewed by ZESA subject matter experts.',
  },
]

export default function WhySection() {
  return (
    <section className="py-16 bg-gray-50">
      <div className="mx-auto max-w-7xl px-4 sm:px-6">
        <h2 className="text-2xl font-bold text-gray-900 text-center mb-12">Why ZESA National Training Centre</h2>
        <div className="grid gap-8 sm:grid-cols-3">
          {features.map(({ icon: Icon, title, desc }) => (
            <div key={title} className="flex flex-col items-center text-center">
              <div className="mb-4 rounded-full bg-primary/10 p-4">
                <Icon className="h-7 w-7 text-primary" />
              </div>
              <h3 className="text-base font-bold text-gray-900 mb-2">{title}</h3>
              <p className="text-sm text-gray-600 max-w-xs">{desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
