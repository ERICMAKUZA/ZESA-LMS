export interface Centre {
  id: string
  name: string
  is_primary: boolean
  location: string
}

export interface User {
  id: number
  email: string
  first_name: string
  last_name: string
  full_name: string
  role: 'STUDENT' | 'REVIEWER' | 'ADMIN' | 'FINANCE' | 'SUPERADMIN' | 'LECTURER' | 'CENTRE_ADMIN'
  employee_id: string
  department: string
  is_active: boolean
  date_joined: string
}

export interface CourseCategory {
  id: number
  name: string
  moodle_id: number | null
}

export interface Course {
  id: number
  fullname: string
  shortname: string
  summary: string
  category: CourseCategory | null
  enrolled_count: number
  max_capacity: number | null
  price: string | null
  thumbnail_url: string
  duration_days: number | null
  level: 'BEGINNER' | 'INTERMEDIATE' | 'ADVANCED' | 'ALL_LEVELS' | null
  is_active: boolean
  is_full: boolean
  requires_approval: boolean
  moodle_course_id: number | null
  created_at: string
  updated_at: string
}

export interface Certificate {
  id: string
  enrollment: string
  user: number
  user_name: string
  course: number
  course_detail: { id: number; fullname: string; shortname: string }
  certificate_number: string
  pdf_url: string
  issued_at: string
}

export interface Report {
  id: string
  title: string
  report_type: string
  generated_by: number
  generated_by_name: string
  parameters: Record<string, unknown>
  file_url: string
  generated_at: string
}

export type ApplicationStatus =
  | 'DRAFT'
  | 'SUBMITTED'
  | 'UNDER_REVIEW'
  | 'MORE_INFO_REQUESTED'
  | 'APPROVED'
  | 'REJECTED'
  | 'PAYMENT_PENDING'
  | 'PAYMENT_CONFIRMED'
  | 'ENROLLED'
  | 'DE_ENROLLED'
  | 'CERTIFIED'

export interface ApplicationDocument {
  id: number
  filename: string
  file: string
  uploaded_at: string
}

export interface ApplicationStatusHistory {
  id: number
  from_status: ApplicationStatus
  to_status: ApplicationStatus
  changed_by: number | null
  changed_by_name: string
  notes: string
  changed_at: string
}

export interface ApplicationPayment {
  id: string
  amount: string
  currency: string
  status: string
  method: string
  confirmed_at: string | null
}

export interface ApplicationEnrollment {
  id: string
  status: string
  enrolled_at: string | null
  moodle_course_url: string
}

export interface Application {
  id: string
  ref: string
  applicant: number
  applicant_name: string
  applicant_email: string
  course: number
  course_name: string
  status: ApplicationStatus
  motivation: string
  line_manager_email: string
  department: string
  employee_id: string
  hexco_level: 'NC' | 'ND' | ''
  student_category: 'DIRECT' | 'APPRENTICE' | 'INTERNAL' | ''
  preferred_centre: string | null
  assigned_centre: string | null
  assigned_centre_name: string | null
  is_resident: boolean
  hostel_name: string
  room_number: string
  guardian_name: string
  guardian_contact: string
  guardian_email: string
  responsible_party: string
  reviewer: number | null
  reviewer_name: string | null
  reviewer_notes: string | null
  rejection_reason: string | null
  more_info_request: string | null
  submitted_at: string | null
  reviewed_at: string | null
  approved_at: string | null
  enrolled_at: string | null
  created_at: string
  updated_at: string
  documents: ApplicationDocument[]
  recent_history: ApplicationStatusHistory[]
  payment: ApplicationPayment | null
  enrollment: ApplicationEnrollment | null
  code_of_conduct_signed: boolean
  code_of_conduct_signed_at: string | null
}

export interface ApplicationListItem {
  id: string
  applicant_name: string
  applicant_email: string
  course_name: string
  status: ApplicationStatus
  submitted_at: string | null
  created_at: string
}

export interface Notification {
  id: number
  recipient: number
  application: string | null
  subject: string
  message: string
  channel: 'EMAIL' | 'SMS' | 'WHATSAPP'
  is_sent: boolean
  sent_at: string | null
  error_message: string
  created_at: string
}

export interface AuthUser {
  id: number
  email: string
  full_name: string
  role: User['role']
  employee_id: string
}

export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface DashboardStats {
  pending_review: number
  under_review: number
  approved_awaiting_payment: number
  enrolled_today: number
  total_this_month: number
  by_status: Partial<Record<ApplicationStatus, number>>
  by_course: { course: string; count: number }[]
  weekly_trend: { day: string; submissions: number }[]
}
