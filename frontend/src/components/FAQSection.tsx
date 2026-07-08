'use client'

import React from 'react'

const FAQS = [
  {
    q: "Who can apply for ZNTC training courses?",
    a: "Our courses are open to ZESA employees (internal students), ZESA apprentices, and direct applicants from the public who work in or wish to enter the energy and engineering sector. Some courses have specific prerequisites — check individual course details.",
  },
  {
    q: "Do I need any qualifications to enrol?",
    a: "Entry requirements vary by course. Short technical courses typically require a relevant trade qualification or work experience. HEXCO National Certificate (NC) and National Diploma (ND) programmes have formal entry requirements which are outlined on each course page.",
  },
  {
    q: "How long are the courses?",
    a: "Course durations range from 2 days (Client Care, Corporate Governance) to 3 weeks (132KV Switching Fundamentals). Most technical courses run for 5 days (one week). Two-week practical courses include Basic Linesman and Domestic Installation. All durations are shown on each course page.",
  },
  {
    q: "How much do the courses cost?",
    a: "Course fees range from USD 240 to USD 1,260 depending on the programme. Standard 5-day courses are USD 325. Two-week practical courses are USD 481. Fees are payable in USD or Zimbabwe Gold (ZiG) at the prevailing interbank rate. Group and corporate discounts may be available — contact us for a quote.",
  },
  {
    q: "Can my company sponsor multiple employees?",
    a: "Yes. We welcome group and corporate bookings. Your company will receive a consolidated quotation covering all nominated employees. Payment can be made as a single company payment which is then allocated per student. Select 'Corporate / Group Booking' when submitting an enquiry.",
  },
  {
    q: "How do I apply?",
    a: "Click 'Apply' on any course page. You will be asked to register (or log in) and complete a short application form. You will need to upload a national ID or passport and your most recent academic certificates. Your application is reviewed by our training coordinators and you will be notified of the outcome within 3 business days.",
  },
  {
    q: "What happens after my application is approved?",
    a: "You will receive a quotation outlining all fees. Once you accept the quotation and payment is confirmed, you will be formally enrolled. Your Moodle learning portal credentials will be emailed to you — this gives you access to course materials, assignments, and your timetable.",
  },
  {
    q: "What is the HEXCO NC and ND programme?",
    a: "HEXCO (Higher Education Examination Council of Zimbabwe) offers nationally recognised qualifications. The National Certificate (NC) is the foundation level and the National Diploma (ND) is the advanced level. ZNTC offers HEXCO programmes in Electrical Engineering, Telecommunications, and Mechanical Engineering.",
  },
  {
    q: "Is accommodation available?",
    a: "Yes. ZNTC has hostel facilities at the Harare campus for students who need to stay on-site during the course. Indicate on your application whether you require accommodation and provide your hostel preference. Accommodation fees are quoted separately.",
  },
  {
    q: "What documents do I need to apply?",
    a: "You will need: a national ID card or passport, your most recent academic or trade certificates, and a passport-size photograph. ZESA apprentices should also provide their apprenticeship registration number. All documents are uploaded securely through the online portal.",
  },
  {
    q: "Can I track my application without logging in?",
    a: "Yes. Once you submit an application you receive a unique reference number (e.g. ZNTC-2026-0042). Visit the Track Application page and enter your reference to check the status at any time — no login required.",
  },
  {
    q: "What if a course is fully booked?",
    a: "Each course runs multiple times throughout the year. If your preferred intake is full, you can apply for the next available intake shown on the course detail page. The system will show you all upcoming dates and their availability.",
  },
  {
    q: "Are there courses in Bulawayo or Kariba?",
    a: "Yes. ZNTC operates three training centres: the primary campus in Harare (Ganges Road, Workington) and satellite centres in Bulawayo and Kariba. During your application you can select your preferred centre. Centre assignment is confirmed at approval stage.",
  },
  {
    q: "How do I get my certificate after completing a course?",
    a: "Certificates are generated digitally upon successful completion of your course and trainer sign-off. You will receive a notification and can download your certificate directly from the student portal. Each certificate has a unique serial number and QR code for verification by employers.",
  },
]

interface Props {
  onEnquire?: () => void
}

export function FAQSection({ onEnquire }: Props) {
  const [openIndex, setOpenIndex] = React.useState<number | null>(null)

  return (
    <section id="faq" className="py-16 bg-gray-50">
      <div className="max-w-3xl mx-auto px-4">
        <h2 className="text-2xl font-bold text-gray-900 text-center mb-2">
          Frequently Asked Questions
        </h2>
        <p className="text-center text-gray-500 mb-10 text-sm">
          Everything you need to know before applying.
        </p>

        <div className="space-y-3">
          {FAQS.map((faq, i) => (
            <div
              key={i}
              className="bg-white rounded-xl border border-gray-200 overflow-hidden hover:border-green-300 transition-colors"
            >
              <button
                onClick={() => setOpenIndex(openIndex === i ? null : i)}
                className="w-full text-left px-5 py-4 flex items-start justify-between gap-3"
              >
                <span className="font-medium text-gray-800 text-sm leading-relaxed">
                  {faq.q}
                </span>
                <span
                  className={`text-green-700 font-bold text-lg flex-shrink-0 transition-transform duration-200 ${
                    openIndex === i ? 'rotate-45' : ''
                  }`}
                >
                  +
                </span>
              </button>
              {openIndex === i && (
                <div className="px-5 pb-5">
                  <p className="text-gray-600 text-sm leading-relaxed">{faq.a}</p>
                </div>
              )}
            </div>
          ))}
        </div>

        <p className="text-center text-sm text-gray-400 mt-10">
          {"Can't find your answer? "}
          {onEnquire ? (
            <button
              onClick={onEnquire}
              className="text-green-700 underline underline-offset-2 hover:text-green-900"
            >
              Send us an enquiry
            </button>
          ) : (
            <a
              href="#enquiry"
              className="text-green-700 underline underline-offset-2 hover:text-green-900"
            >
              Send us an enquiry
            </a>
          )}
        </p>
      </div>
    </section>
  )
}
