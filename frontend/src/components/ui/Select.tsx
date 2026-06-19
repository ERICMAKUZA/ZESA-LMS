'use client'

import * as RadixSelect from '@radix-ui/react-select'
import { ChevronDown, Check } from 'lucide-react'
import { clsx } from 'clsx'

export interface SelectOption {
  value: string
  label: string
}

interface SelectProps {
  label?: string
  error?: string
  placeholder?: string
  options: SelectOption[]
  value?: string
  onValueChange?: (value: string) => void
  disabled?: boolean
  id?: string
}

export default function Select({
  label,
  error,
  placeholder = 'Select…',
  options,
  value,
  onValueChange,
  disabled,
  id,
}: SelectProps) {
  const selectId = id ?? label?.toLowerCase().replace(/\s+/g, '-')
  return (
    <div className="flex flex-col gap-1">
      {label && (
        <label htmlFor={selectId} className="text-sm font-medium text-gray-700">
          {label}
        </label>
      )}
      <RadixSelect.Root value={value} onValueChange={onValueChange} disabled={disabled}>
        <RadixSelect.Trigger
          id={selectId}
          className={clsx(
            'flex w-full items-center justify-between rounded-md border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm',
            'focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary',
            error && 'border-danger focus:ring-danger',
            disabled && 'cursor-not-allowed opacity-50',
          )}
        >
          <RadixSelect.Value placeholder={placeholder} />
          <RadixSelect.Icon>
            <ChevronDown className="h-4 w-4 text-gray-500" />
          </RadixSelect.Icon>
        </RadixSelect.Trigger>
        <RadixSelect.Portal>
          <RadixSelect.Content className="z-50 min-w-[8rem] overflow-hidden rounded-md border border-gray-200 bg-white shadow-md">
            <RadixSelect.Viewport className="p-1">
              {options.map((opt) => (
                <RadixSelect.Item
                  key={opt.value}
                  value={opt.value}
                  className="relative flex cursor-default select-none items-center rounded-sm py-1.5 pl-8 pr-3 text-sm outline-none hover:bg-primary/10 focus:bg-primary/10 data-[disabled]:pointer-events-none data-[disabled]:opacity-50"
                >
                  <RadixSelect.ItemIndicator className="absolute left-2 flex items-center">
                    <Check className="h-4 w-4 text-primary" />
                  </RadixSelect.ItemIndicator>
                  <RadixSelect.ItemText>{opt.label}</RadixSelect.ItemText>
                </RadixSelect.Item>
              ))}
            </RadixSelect.Viewport>
          </RadixSelect.Content>
        </RadixSelect.Portal>
      </RadixSelect.Root>
      {error && <p className="text-xs text-danger">{error}</p>}
    </div>
  )
}
