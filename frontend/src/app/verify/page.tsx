'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Award } from 'lucide-react'
import PublicLayout from '@/components/layout/PublicLayout'
import Card from '@/components/ui/Card'
import Input from '@/components/ui/Input'
import Button from '@/components/ui/Button'

export default function VerifyLandingPage() {
  const [certId, setCertId] = useState('')
  const router = useRouter()

  const goVerify = () => {
    if (certId.trim()) router.push(`/verify/${certId.trim()}`)
  }

  return (
    <PublicLayout>
      <div className="flex min-h-[70vh] items-center justify-center px-4">
        <div className="w-full max-w-md">
          <Card>
            <div className="flex flex-col items-center py-6 text-center">
              <Award className="h-10 w-10 text-primary mb-3" />
              <h1 className="text-xl font-bold text-gray-900 mb-1">Verify a Certificate</h1>
              <p className="text-sm text-gray-500 mb-6">
                Enter the certificate number from a ZNTC certificate to confirm its authenticity.
              </p>

              <div className="w-full">
                <Input
                  placeholder="e.g. ZNTC-CERT-2026-0001"
                  value={certId}
                  onChange={(e) => setCertId(e.target.value.toUpperCase())}
                  onKeyDown={(e) => e.key === 'Enter' && goVerify()}
                  className="text-center font-mono"
                />
              </div>

              <Button className="mt-4 w-full" size="lg" onClick={goVerify} disabled={!certId.trim()}>
                Verify Certificate
              </Button>
            </div>
          </Card>
        </div>
      </div>
    </PublicLayout>
  )
}
