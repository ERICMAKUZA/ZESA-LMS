'use client'

import { useRef, useState } from 'react'
import StudentLayout from '@/components/layout/StudentLayout'
import PageHeader from '@/components/ui/PageHeader'
import Card from '@/components/ui/Card'
import Spinner from '@/components/ui/Spinner'
import { useToast } from '@/components/ui/Toast'
import { useAuth } from '@/hooks/useAuth'
import { useMyApplications, useApplication, useUpdatePhoto } from '@/hooks/useApplications'
import Link from 'next/link'

const MAX_PHOTO_SIZE = 5 * 1024 * 1024
const ACCEPTED_TYPES = ['image/jpeg', 'image/png']

export default function ProfilePage() {
  const { user } = useAuth()
  const { toast } = useToast()
  const { data: applications, isLoading: applicationsLoading } = useMyApplications()
  const latest = applications?.results?.[0]

  const { data: application, isLoading: applicationLoading } = useApplication(latest?.id ?? '')
  const updatePhoto = useUpdatePhoto(latest?.id ?? '')
  const fileInputRef = useRef<HTMLInputElement>(null)

  const [uploading, setUploading] = useState(false)

  const handlePhotoChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    e.target.value = ''
    if (!file) return

    if (file.size > MAX_PHOTO_SIZE) {
      toast({ variant: 'error', title: 'Photo too large', description: 'Must be under 5MB.' })
      return
    }
    if (!ACCEPTED_TYPES.includes(file.type)) {
      toast({ variant: 'error', title: 'Unsupported format', description: 'JPG or PNG only.' })
      return
    }

    setUploading(true)
    try {
      await updatePhoto.mutateAsync(file)
      toast({ variant: 'success', title: 'Photo updated.' })
    } catch {
      toast({ variant: 'error', title: 'Upload failed', description: 'Could not update your photo.' })
    } finally {
      setUploading(false)
    }
  }

  const isLoading = applicationsLoading || (!!latest && applicationLoading)

  return (
    <StudentLayout>
      <PageHeader title="My Profile" subtitle="Your account details and passport photo" />

      <Card>
        {isLoading ? (
          <div className="flex justify-center py-10">
            <Spinner className="text-primary" />
          </div>
        ) : !latest ? (
          <div className="py-10 text-center text-sm text-gray-500">
            <p>Your photo is captured as part of a course application.</p>
            <p className="mt-1">
              <Link href="/courses" className="font-medium text-primary hover:underline">
                Apply for a course
              </Link>{' '}
              to add one.
            </p>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3 border-b border-gray-100 pb-8">
            <div className="relative">
              {application?.student_photo ? (
                <img
                  src={application.student_photo}
                  alt="Profile photo"
                  className="h-24 w-24 rounded-full border-4 border-primary/10 object-cover"
                />
              ) : (
                <div className="flex h-24 w-24 items-center justify-center rounded-full border-4 border-primary/10 bg-primary/5">
                  <span className="text-3xl font-bold text-primary">
                    {user?.full_name?.[0]?.toUpperCase() ?? '?'}
                  </span>
                </div>
              )}
              <label
                htmlFor="photo-upload"
                className="absolute bottom-0 right-0 flex h-8 w-8 cursor-pointer items-center justify-center rounded-full border-2 border-white bg-primary hover:bg-primary-dark"
              >
                {uploading ? <Spinner size="sm" className="text-white" /> : <span className="text-sm text-white">+</span>}
              </label>
              <input
                id="photo-upload"
                ref={fileInputRef}
                type="file"
                accept="image/jpeg,image/png"
                className="hidden"
                disabled={uploading}
                onChange={handlePhotoChange}
              />
            </div>
            <p className="text-xs text-gray-400">Passport-size photo · JPG or PNG · Max 5MB</p>
            <p className="text-xs text-gray-400">Used on your application to {latest.course_name}</p>
          </div>
        )}

        <div className="grid gap-4 pt-6 sm:grid-cols-2">
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-gray-400">Full name</p>
            <p className="mt-1 text-sm text-gray-900">{user?.full_name}</p>
          </div>
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-gray-400">Email</p>
            <p className="mt-1 text-sm text-gray-900">{user?.email}</p>
          </div>
        </div>
      </Card>
    </StudentLayout>
  )
}
