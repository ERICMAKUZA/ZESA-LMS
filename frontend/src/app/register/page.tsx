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
  first_name: z.string().min(1, 'Required'),
  last_name: z.string().min(1, 'Required'),
  email: z.string().email('Enter a valid email'),
  employee_id: z.string().optional(),
  department: z.string().optional(),
  password: z.string().min(8, 'At least 8 characters'),
  confirm_password: z.string(),
}).refine((d) => d.password === d.confirm_password, {
  path: ['confirm_password'],
  message: 'Passwords do not match',
})

type FormValues = z.infer<typeof schema>

export default function RegisterPage() {
  const { register: registerUser } = useAuth()
  const { toast } = useToast()
  const router = useRouter()

  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormValues>({
    resolver: zodResolver(schema),
  })

  const onSubmit = async (values: FormValues) => {
    try {
      const { confirm_password: _, ...payload } = values
      await registerUser(payload)
      toast({ variant: 'success', title: 'Account created', description: 'You can now sign in.' })
      router.push('/login')
    } catch {
      toast({ variant: 'error', title: 'Registration failed', description: 'Please check your details and try again.' })
    }
  }

  return (
    <PublicLayout>
      <div className="flex min-h-[80vh] items-center justify-center px-4 py-10">
        <div className="w-full max-w-md">
          <div className="rounded-xl border border-gray-200 bg-white p-8 shadow-sm">
            <h2 className="text-2xl font-bold text-center text-gray-900 mb-6">Create account</h2>
            <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
              <div className="grid grid-cols-2 gap-3">
                <Input label="First name" error={errors.first_name?.message} {...register('first_name')} />
                <Input label="Last name"  error={errors.last_name?.message}  {...register('last_name')} />
              </div>
              <Input label="Email"       type="email" error={errors.email?.message}       {...register('email')} />
              <Input label="Employee ID" error={errors.employee_id?.message} helper="Optional — will be auto-filled from HR records." {...register('employee_id')} />
              <Input label="Department"  error={errors.department?.message}  {...register('department')} />
              <Input label="Password"    type="password" error={errors.password?.message} {...register('password')} />
              <Input label="Confirm password" type="password" error={errors.confirm_password?.message} {...register('confirm_password')} />
              <Button type="submit" loading={isSubmitting} className="mt-2">Create account</Button>
            </form>
            <p className="mt-4 text-center text-sm text-gray-600">
              Already have an account?{' '}
              <Link href="/login" className="font-medium text-primary hover:underline">Sign in</Link>
            </p>
          </div>
        </div>
      </div>
    </PublicLayout>
  )
}
