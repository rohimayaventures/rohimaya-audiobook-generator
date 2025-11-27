import Link from 'next/link'
import { Footer } from '@/components/layout'

/**
 * Privacy Policy Page - AuthorFlow Studios
 * Production-ready privacy policy for Colorado, USA jurisdiction
 */
export default function PrivacyPage() {
  return (
    <div className="min-h-screen flex flex-col">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 backdrop-blur-xl bg-af-midnight/60 border-b border-af-card-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link href="/" className="font-serif text-xl font-bold text-gradient">
              AuthorFlow
            </Link>
            <div className="flex items-center gap-4">
              <Link href="/pricing" className="text-sm text-white/70 hover:text-white transition-colors">
                Pricing
              </Link>
              <Link href="/login" className="text-sm font-medium text-white/80 hover:text-white transition-colors">
                Log in
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="flex-1 pt-24 pb-16 px-4">
        <div className="max-w-3xl mx-auto">
          <h1 className="text-4xl font-bold text-white mb-4">Privacy Policy</h1>
          <p className="text-white/60 mb-8">Last updated: November 27, 2025</p>

          <div className="prose prose-invert prose-lg max-w-none space-y-8">
            {/* Introduction */}
            <section>
              <h2 className="text-2xl font-semibold text-white mb-4">Introduction</h2>
              <p className="text-white/80 leading-relaxed">
                AuthorFlow Studios (&quot;we,&quot; &quot;our,&quot; or &quot;us&quot;) is a product of Rohimaya Publishing,
                a division of Pagade Ventures, LLC, operating from the State of Colorado, United States. We are committed
                to protecting your privacy and handling your personal information with care and respect.
              </p>
              <p className="text-white/80 leading-relaxed mt-4">
                This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you
                use our web application and services at authorflowstudios.rohimayapublishing.com (the &quot;Service&quot;).
                Please read this policy carefully. By using the Service, you consent to the practices described herein.
              </p>
            </section>

            {/* Information We Collect */}
            <section>
              <h2 className="text-2xl font-semibold text-white mb-4">Information We Collect</h2>

              <h3 className="text-xl font-medium text-white mb-3">Account Information</h3>
              <p className="text-white/80 leading-relaxed">
                When you create an account, we collect:
              </p>
              <ul className="list-disc list-inside text-white/80 space-y-2 mt-2">
                <li>Your name and email address</li>
                <li>Authentication credentials and identifiers</li>
                <li>Profile information you choose to provide</li>
                <li>OAuth data if you sign in via Google or other providers</li>
              </ul>

              <h3 className="text-xl font-medium text-white mb-3 mt-6">Billing Information</h3>
              <p className="text-white/80 leading-relaxed">
                Payment processing is handled by Stripe, Inc. We do not store your complete credit card numbers
                or banking details on our servers. Stripe collects and processes your payment information in
                accordance with their privacy policy. We receive and store:
              </p>
              <ul className="list-disc list-inside text-white/80 space-y-2 mt-2">
                <li>Billing name and address</li>
                <li>Last four digits of your payment card</li>
                <li>Transaction history and subscription status</li>
              </ul>

              <h3 className="text-xl font-medium text-white mb-3 mt-6">Content You Provide</h3>
              <p className="text-white/80 leading-relaxed">
                To provide our audiobook generation services, we collect and process:
              </p>
              <ul className="list-disc list-inside text-white/80 space-y-2 mt-2">
                <li>Manuscripts and text files you upload</li>
                <li>Documents imported from Google Drive or Google Docs</li>
                <li>Generated audio files and audiobook outputs</li>
                <li>Cover images and associated metadata</li>
                <li>Project settings and voice preferences</li>
              </ul>

              <h3 className="text-xl font-medium text-white mb-3 mt-6">Usage Information</h3>
              <p className="text-white/80 leading-relaxed">
                We automatically collect certain information when you use the Service:
              </p>
              <ul className="list-disc list-inside text-white/80 space-y-2 mt-2">
                <li>IP address and approximate geographic location</li>
                <li>Browser type, device information, and operating system</li>
                <li>Pages visited and features used</li>
                <li>Timestamps and session duration</li>
                <li>Error logs and performance data</li>
              </ul>
            </section>

            {/* How We Use Your Information */}
            <section>
              <h2 className="text-2xl font-semibold text-white mb-4">How We Use Your Information</h2>
              <p className="text-white/80 leading-relaxed">
                We use the information we collect to:
              </p>
              <ul className="list-disc list-inside text-white/80 space-y-2 mt-2">
                <li>Provide, maintain, and improve the Service</li>
                <li>Process your manuscripts through AI text-to-speech conversion</li>
                <li>Generate audiobooks with emotional narration and multi-character voices</li>
                <li>Parse and analyze manuscript structure, chapters, and content</li>
                <li>Create retail samples and cover image prompts</li>
                <li>Process payments and manage your subscription</li>
                <li>Send you transactional emails (confirmations, receipts, account updates)</li>
                <li>Respond to your inquiries and provide customer support</li>
                <li>Detect, prevent, and address technical issues or security threats</li>
                <li>Comply with legal obligations</li>
              </ul>
            </section>

            {/* Third-Party Services */}
            <section>
              <h2 className="text-2xl font-semibold text-white mb-4">Third-Party Service Providers</h2>
              <p className="text-white/80 leading-relaxed">
                We share your information with trusted third-party service providers who assist us in
                operating the Service:
              </p>

              <h3 className="text-xl font-medium text-white mb-3 mt-6">AI Processing</h3>
              <p className="text-white/80 leading-relaxed">
                Your manuscript text is transmitted to OpenAI and other AI service providers to generate
                audiobook narration, analyze content structure, and create AI-powered features. These
                providers process your content in accordance with their privacy policies and data
                processing agreements.
              </p>

              <h3 className="text-xl font-medium text-white mb-3 mt-6">Payments</h3>
              <p className="text-white/80 leading-relaxed">
                Stripe, Inc. processes all payment transactions. Your billing information is transmitted
                directly to Stripe and handled according to their privacy policy and PCI-DSS compliance standards.
              </p>

              <h3 className="text-xl font-medium text-white mb-3 mt-6">Storage</h3>
              <p className="text-white/80 leading-relaxed">
                Your manuscripts and generated audio files are stored using Cloudflare R2 object storage.
                Account and metadata information is stored using Supabase database services.
              </p>

              <h3 className="text-xl font-medium text-white mb-3 mt-6">Authentication</h3>
              <p className="text-white/80 leading-relaxed">
                We use Supabase for authentication services. If you choose to sign in with Google,
                authentication data is processed through Google&apos;s OAuth services.
              </p>
            </section>

            {/* Google API Disclosure */}
            <section>
              <h2 className="text-2xl font-semibold text-white mb-4">Google API Services Disclosure</h2>
              <p className="text-white/80 leading-relaxed">
                AuthorFlow Studios&apos; use and transfer of information received from Google APIs adheres to the{' '}
                <a
                  href="https://developers.google.com/terms/api-services-user-data-policy"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-af-lavender hover:text-white underline"
                >
                  Google API Services User Data Policy
                </a>
                , including the Limited Use requirements.
              </p>
              <p className="text-white/80 leading-relaxed mt-4">
                When you connect your Google Drive or Google Docs account:
              </p>
              <ul className="list-disc list-inside text-white/80 space-y-2 mt-2">
                <li>We request read-only access to files you explicitly select for import</li>
                <li>We only access and retrieve documents you specifically choose to import into AuthorFlow Studios</li>
                <li>We do not access, scan, or index files you have not selected</li>
                <li>We do not share your Google data with third parties except as necessary to provide the Service</li>
                <li>You can revoke access at any time through your Google account settings</li>
              </ul>
            </section>

            {/* Data Retention */}
            <section>
              <h2 className="text-2xl font-semibold text-white mb-4">Data Retention</h2>
              <p className="text-white/80 leading-relaxed">
                We retain your information for as long as necessary to provide the Service and fulfill
                the purposes described in this policy:
              </p>
              <ul className="list-disc list-inside text-white/80 space-y-2 mt-2">
                <li>
                  <strong className="text-white">Account data:</strong> Retained while your account is active
                  and for a reasonable period thereafter
                </li>
                <li>
                  <strong className="text-white">Manuscripts and audio files:</strong> Retained in cloud storage
                  while your account is active
                </li>
                <li>
                  <strong className="text-white">Billing records:</strong> Retained as required for tax,
                  accounting, and legal compliance purposes
                </li>
                <li>
                  <strong className="text-white">Usage logs:</strong> Typically retained for 90 days for
                  analytics and troubleshooting
                </li>
              </ul>
              <p className="text-white/80 leading-relaxed mt-4">
                We reserve the right to delete inactive projects and associated files after an extended
                period of account inactivity, with prior notice to registered email addresses.
              </p>
            </section>

            {/* Data Security */}
            <section>
              <h2 className="text-2xl font-semibold text-white mb-4">Data Security</h2>
              <p className="text-white/80 leading-relaxed">
                We implement reasonable technical and organizational measures to protect your personal
                information, including:
              </p>
              <ul className="list-disc list-inside text-white/80 space-y-2 mt-2">
                <li>Encryption of data in transit using TLS/SSL</li>
                <li>Secure authentication with session management</li>
                <li>Access controls limiting employee access to personal data</li>
                <li>Regular security assessments of our systems</li>
              </ul>
              <p className="text-white/80 leading-relaxed mt-4">
                However, no method of transmission over the Internet or electronic storage is 100% secure.
                While we strive to protect your information, we cannot guarantee absolute security.
              </p>
            </section>

            {/* International Transfers */}
            <section>
              <h2 className="text-2xl font-semibold text-white mb-4">International Data Transfers</h2>
              <p className="text-white/80 leading-relaxed">
                Your information may be transferred to, stored, and processed in the United States and
                other countries where our service providers operate. These countries may have data
                protection laws that differ from the laws of your country. By using the Service, you
                consent to the transfer of your information to these countries.
              </p>
            </section>

            {/* Children's Privacy */}
            <section>
              <h2 className="text-2xl font-semibold text-white mb-4">Children&apos;s Privacy</h2>
              <p className="text-white/80 leading-relaxed">
                The Service is not directed to children under the age of 13, and we do not knowingly
                collect personal information from children under 13. If we become aware that we have
                collected personal information from a child under 13, we will take steps to delete
                such information promptly.
              </p>
              <p className="text-white/80 leading-relaxed mt-4">
                Users between the ages of 13 and 17 may use the Service with the consent and supervision
                of a parent or legal guardian. The Service is primarily designed for adult authors,
                publishers, and content creators.
              </p>
            </section>

            {/* Your Rights */}
            <section>
              <h2 className="text-2xl font-semibold text-white mb-4">Your Rights and Choices</h2>
              <p className="text-white/80 leading-relaxed">
                Depending on your location, you may have certain rights regarding your personal information:
              </p>
              <ul className="list-disc list-inside text-white/80 space-y-2 mt-2">
                <li>
                  <strong className="text-white">Access:</strong> Request a copy of the personal
                  information we hold about you
                </li>
                <li>
                  <strong className="text-white">Correction:</strong> Request that we correct inaccurate
                  or incomplete information
                </li>
                <li>
                  <strong className="text-white">Deletion:</strong> Request that we delete your personal
                  information, subject to certain exceptions
                </li>
                <li>
                  <strong className="text-white">Export:</strong> Request a portable copy of your data
                </li>
                <li>
                  <strong className="text-white">Opt-out:</strong> Unsubscribe from marketing emails using
                  the link provided in each message
                </li>
              </ul>
              <p className="text-white/80 leading-relaxed mt-4">
                To exercise these rights, please contact us at{' '}
                <a
                  href="mailto:support@authorflowstudios.rohimayapublishing.com"
                  className="text-af-lavender hover:text-white underline"
                >
                  support@authorflowstudios.rohimayapublishing.com
                </a>
                . We will respond to your request within a reasonable timeframe.
              </p>
            </section>

            {/* Changes to This Policy */}
            <section>
              <h2 className="text-2xl font-semibold text-white mb-4">Changes to This Policy</h2>
              <p className="text-white/80 leading-relaxed">
                We may update this Privacy Policy from time to time to reflect changes in our practices
                or for legal, operational, or regulatory reasons. We will post the revised policy on
                this page with an updated &quot;Last updated&quot; date. We encourage you to review this
                policy periodically. Your continued use of the Service after any changes constitutes
                your acceptance of the updated policy.
              </p>
            </section>

            {/* Contact Information */}
            <section>
              <h2 className="text-2xl font-semibold text-white mb-4">Contact Us</h2>
              <p className="text-white/80 leading-relaxed">
                If you have any questions, concerns, or requests regarding this Privacy Policy or our
                data practices, please contact us:
              </p>
              <div className="mt-4 p-4 bg-af-card/50 rounded-lg border border-af-card-border">
                <p className="text-white font-medium">AuthorFlow Studios</p>
                <p className="text-white/70">A product of Rohimaya Publishing / Pagade Ventures, LLC</p>
                <p className="text-white/70 mt-2">
                  Email:{' '}
                  <a
                    href="mailto:support@authorflowstudios.rohimayapublishing.com"
                    className="text-af-lavender hover:text-white"
                  >
                    support@authorflowstudios.rohimayapublishing.com
                  </a>
                </p>
                <p className="text-white/70">Location: Colorado, United States</p>
              </div>
            </section>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  )
}
