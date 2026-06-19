'use client'

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import PublicLayout from '@/components/layout/PublicLayout'
import Input from '@/components/ui/Input'
import Button from '@/components/ui/Button'
import { useToast } from '@/components/ui/Toast'
import { useAuth } from '@/hooks/useAuth'

const schema = z.object({
  email: z.string().email('Enter a valid email'),
  password: z.string().min(1, 'Password is required'),
})

type FormValues = z.infer<typeof schema>

export default function LoginPage() {
  const { login } = useAuth()
  const { toast } = useToast()
  const router = useRouter()

  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormValues>({
    resolver: zodResolver(schema),
  })

  const onSubmit = async (values: FormValues) => {
    try {
      const user = await login(values.email, values.password)
      const isAdmin = user && ['ADMIN', 'REVIEWER', 'SUPERADMIN', 'FINANCE'].includes(user.role)
      router.push(isAdmin ? '/admin' : '/dashboard')
    } catch {
      toast({ variant: 'error', title: 'Login failed', description: 'Invalid email or password.' })
    }
  }

  return (
    <PublicLayout>
      <div className="flex min-h-[70vh] items-center justify-center px-4">
        <div className="w-full max-w-md">
          <div className="rounded-xl border border-gray-200 bg-white p-8 shadow-sm">
            <h2 className="text-2xl font-bold text-center text-gray-900 mb-6">Sign in</h2>
            <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
              <Input
                label="Email"
                type="email"
                autoComplete="email"
                error={errors.email?.message}
                {...register('email')}
              />
              <Input
                label="Password"
                type="password"
                autoComplete="current-password"
                error={errors.password?.message}
                {...register('password')}
              />
              <Button type="submit" loading={isSubmitting} className="mt-2">
                Sign in
              </Button>
            </form>
            <p className="mt-4 text-center text-sm text-gray-600">
              Don&apos;t have an account?{' '}
              <Link href="/register" className="font-medium text-primary hover:underline">
                Register
              </Link>
            </p>
          </div>
        </div>
      </div>
    </PublicLayout>
  )
}
