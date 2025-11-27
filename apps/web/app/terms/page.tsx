import Link from 'next/link'
import { Footer } from '@/components/layout'

/**
 * Terms of Use Page - AuthorFlow Studios
 * Production-ready terms of service for Colorado, USA jurisdiction
 */
export default function TermsPage() {
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
          <h1 className="text-4xl font-bold text-white mb-4">Terms of Use</h1>
          <p className="text-white/60 mb-8">Last updated: November 27, 2025</p>

          <div className="prose prose-invert prose-lg max-w-none space-y-8">
            {/* Agreement to Terms */}
            <section>
              <h2 className="text-2xl font-semibold text-white mb-4">Agreement to Terms</h2>
              <p className="text-white/80 leading-relaxed">
                Welcome to AuthorFlow Studios. These Terms of Use (&quot;Terms&quot;) constitute a legally
                binding agreement between you (&quot;you&quot; or &quot;User&quot;) and AuthorFlow Studios,
                a product of Rohimaya Publishing, a division of Pagade Ventures, LLC (&quot;we,&quot;
                &quot;our,&quot; or &quot;us&quot;), governing your access to and use of our web application
                and services (collectively, the &quot;Service&quot;).
              </p>
              <p className="text-white/80 leading-relaxed mt-4">
                By accessing or using the Service, you agree to be bound by these Terms and our{' '}
                <Link href="/privacy" className="text-af-lavender hover:text-white underline">
                  Privacy Policy
                </Link>
                . If you do not agree to these Terms, you may not access or use the Service.
              </p>
            </section>

            {/* Service Description */}
            <section>
              <h2 className="text-2xl font-semibold text-white mb-4">Description of Service</h2>
              <p className="text-white/80 leading-relaxed">
                AuthorFlow Studios is a web-based platform that helps authors, publishers, and content
                creators transform written manuscripts into professionally produced audiobooks using
                artificial intelligence technology. Our services include:
              </p>
              <ul className="list-disc list-inside text-white/80 space-y-2 mt-2">
                <li>AI-powered text-to-speech audiobook generation</li>
                <li>Multi-character and emotional voice narration</li>
                <li>Manuscript parsing and chapter organization</li>
                <li>Retail sample and cover prompt generation</li>
                <li>Audio file export in various formats</li>
                <li>Integration with Google Drive and Google Docs</li>
              </ul>
            </section>

            {/* Account Registration */}
            <section>
              <h2 className="text-2xl font-semibold text-white mb-4">Account Registration and Security</h2>
              <p className="text-white/80 leading-relaxed">
                To use certain features of the Service, you must create an account. When registering,
                you agree to:
              </p>
              <ul className="list-disc list-inside text-white/80 space-y-2 mt-2">
                <li>Provide accurate, current, and complete information</li>
                <li>Maintain and promptly update your account information</li>
                <li>Keep your password secure and confidential</li>
                <li>Notify us immediately of any unauthorized access to your account</li>
                <li>Accept responsibility for all activities that occur under your account</li>
              </ul>
              <p className="text-white/80 leading-relaxed mt-4">
                You must be at least 18 years old, or between 13 and 17 with parental consent, to create
                an account. We reserve the right to suspend or terminate accounts that violate these Terms
                or engage in fraudulent, abusive, or illegal activity.
              </p>
            </section>

            {/* User Content and Ownership */}
            <section>
              <h2 className="text-2xl font-semibold text-white mb-4">User Content and Intellectual Property</h2>

              <h3 className="text-xl font-medium text-white mb-3">Your Content</h3>
              <p className="text-white/80 leading-relaxed">
                You retain full ownership of your manuscripts, text, and any original content you upload
                to the Service (&quot;User Content&quot;). You also own the resulting audio files generated
                from your content, subject to these Terms.
              </p>

              <h3 className="text-xl font-medium text-white mb-3 mt-6">License Grant</h3>
              <p className="text-white/80 leading-relaxed">
                By uploading User Content to the Service, you grant us a limited, non-exclusive,
                royalty-free, worldwide license to:
              </p>
              <ul className="list-disc list-inside text-white/80 space-y-2 mt-2">
                <li>Store, process, and transmit your content as necessary to provide the Service</li>
                <li>Send your content to third-party AI providers for processing</li>
                <li>Create derivative works (such as audiobook narration) from your content</li>
                <li>Display content previews and samples within your account</li>
              </ul>
              <p className="text-white/80 leading-relaxed mt-4">
                This license terminates when you delete your content from the Service, except for backup
                copies retained for a reasonable period and content processed by third-party services.
              </p>

              <h3 className="text-xl font-medium text-white mb-3 mt-6">Your Representations</h3>
              <p className="text-white/80 leading-relaxed">
                By uploading User Content, you represent and warrant that:
              </p>
              <ul className="list-disc list-inside text-white/80 space-y-2 mt-2">
                <li>You own or have the necessary rights and permissions to use the content</li>
                <li>Your content does not infringe upon any third-party copyrights, trademarks, or other intellectual property rights</li>
                <li>Your content does not violate any applicable laws or regulations</li>
                <li>You have obtained all necessary consents from any persons depicted or mentioned in your content</li>
              </ul>
            </section>

            {/* AI Technology Disclaimer */}
            <section>
              <h2 className="text-2xl font-semibold text-white mb-4">AI Technology and Limitations</h2>
              <p className="text-white/80 leading-relaxed">
                The Service uses artificial intelligence and machine learning technologies to generate
                audio narration. You acknowledge and agree that:
              </p>
              <ul className="list-disc list-inside text-white/80 space-y-2 mt-2">
                <li>AI-generated output may contain errors, inaccuracies, or unexpected results</li>
                <li>You are solely responsible for reviewing and editing all generated content before publication or distribution</li>
                <li>We do not guarantee that AI output will be error-free, commercially viable, or suitable for any particular purpose</li>
                <li>We are not liable for any decisions, actions, or consequences based on AI-generated content</li>
                <li>AI voices are synthetic and may not perfectly replicate human speech patterns</li>
              </ul>
              <p className="text-white/80 leading-relaxed mt-4">
                You should always review, verify, and approve all generated audiobook content before
                publishing or distributing it to any platforms or audiences.
              </p>
            </section>

            {/* Prohibited Uses */}
            <section>
              <h2 className="text-2xl font-semibold text-white mb-4">Prohibited Uses</h2>
              <p className="text-white/80 leading-relaxed">
                You agree not to use the Service to:
              </p>
              <ul className="list-disc list-inside text-white/80 space-y-2 mt-2">
                <li>Upload or transmit content that is illegal, harmful, threatening, abusive, harassing, defamatory, vulgar, obscene, or otherwise objectionable</li>
                <li>Create content that promotes violence, discrimination, or hatred against any individual or group</li>
                <li>Generate content that infringes upon intellectual property rights or violates the rights of others</li>
                <li>Impersonate any person or entity, or misrepresent your affiliation with any person or entity</li>
                <li>Upload malware, viruses, or any code designed to harm or compromise the Service</li>
                <li>Attempt to gain unauthorized access to the Service, other accounts, or connected systems</li>
                <li>Reverse engineer, decompile, or disassemble any portion of the Service</li>
                <li>Use automated systems (bots, scrapers) to access the Service without authorization</li>
                <li>Interfere with or disrupt the integrity or performance of the Service</li>
                <li>Circumvent usage limits, billing, or access controls</li>
              </ul>
              <p className="text-white/80 leading-relaxed mt-4">
                Violation of these prohibitions may result in immediate termination of your account
                and may be reported to appropriate authorities.
              </p>
            </section>

            {/* Payments and Billing */}
            <section>
              <h2 className="text-2xl font-semibold text-white mb-4">Payments, Billing, and Subscriptions</h2>

              <h3 className="text-xl font-medium text-white mb-3">Subscription Plans</h3>
              <p className="text-white/80 leading-relaxed">
                The Service offers various subscription tiers with different features and usage limits.
                By subscribing to a paid plan, you agree to pay the applicable fees as described on our{' '}
                <Link href="/pricing" className="text-af-lavender hover:text-white underline">
                  Pricing page
                </Link>
                .
              </p>

              <h3 className="text-xl font-medium text-white mb-3 mt-6">Payment Processing</h3>
              <p className="text-white/80 leading-relaxed">
                All payments are processed by Stripe, Inc. By providing payment information, you authorize
                us to charge your payment method for subscription fees and any applicable taxes. You agree
                to Stripe&apos;s terms of service and privacy policy.
              </p>

              <h3 className="text-xl font-medium text-white mb-3 mt-6">Automatic Renewal</h3>
              <p className="text-white/80 leading-relaxed">
                Subscriptions automatically renew at the end of each billing period unless cancelled.
                You may cancel your subscription at any time through your billing settings or the
                Stripe customer portal. Cancellation takes effect at the end of the current billing period.
              </p>

              <h3 className="text-xl font-medium text-white mb-3 mt-6">Plan Changes</h3>
              <p className="text-white/80 leading-relaxed">
                You may upgrade or downgrade your subscription plan at any time. Upgrades take effect
                immediately with prorated charges. Downgrades take effect at the start of your next
                billing period.
              </p>

              <h3 className="text-xl font-medium text-white mb-3 mt-6">Refunds</h3>
              <p className="text-white/80 leading-relaxed">
                Please see our{' '}
                <Link href="/refund" className="text-af-lavender hover:text-white underline">
                  Refund Policy
                </Link>{' '}
                for information about refunds and cancellations.
              </p>
            </section>

            {/* Disclaimer of Warranties */}
            <section>
              <h2 className="text-2xl font-semibold text-white mb-4">Disclaimer of Warranties</h2>
              <p className="text-white/80 leading-relaxed uppercase text-sm">
                THE SERVICE IS PROVIDED &quot;AS IS&quot; AND &quot;AS AVAILABLE&quot; WITHOUT WARRANTIES
                OF ANY KIND, EITHER EXPRESS OR IMPLIED. TO THE FULLEST EXTENT PERMITTED BY LAW, WE
                DISCLAIM ALL WARRANTIES, INCLUDING BUT NOT LIMITED TO IMPLIED WARRANTIES OF
                MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, TITLE, AND NON-INFRINGEMENT.
              </p>
              <p className="text-white/80 leading-relaxed uppercase text-sm mt-4">
                WE DO NOT WARRANT THAT THE SERVICE WILL BE UNINTERRUPTED, ERROR-FREE, SECURE, OR FREE
                OF VIRUSES OR OTHER HARMFUL COMPONENTS. WE DO NOT WARRANT THAT ANY DEFECTS WILL BE
                CORRECTED OR THAT THE SERVICE WILL MEET YOUR REQUIREMENTS OR EXPECTATIONS.
              </p>
            </section>

            {/* Limitation of Liability */}
            <section>
              <h2 className="text-2xl font-semibold text-white mb-4">Limitation of Liability</h2>
              <p className="text-white/80 leading-relaxed uppercase text-sm">
                TO THE MAXIMUM EXTENT PERMITTED BY APPLICABLE LAW, IN NO EVENT SHALL AUTHORFLOW STUDIOS,
                ROHIMAYA PUBLISHING, PAGADE VENTURES, LLC, OR THEIR OFFICERS, DIRECTORS, EMPLOYEES,
                AGENTS, OR AFFILIATES BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL,
                OR PUNITIVE DAMAGES, INCLUDING WITHOUT LIMITATION LOSS OF PROFITS, DATA, USE, GOODWILL,
                OR OTHER INTANGIBLE LOSSES, RESULTING FROM:
              </p>
              <ul className="list-disc list-inside text-white/80 space-y-2 mt-4 uppercase text-sm">
                <li>YOUR ACCESS TO OR USE OF (OR INABILITY TO ACCESS OR USE) THE SERVICE</li>
                <li>ANY CONDUCT OR CONTENT OF ANY THIRD PARTY ON THE SERVICE</li>
                <li>ANY CONTENT OBTAINED FROM THE SERVICE</li>
                <li>UNAUTHORIZED ACCESS, USE, OR ALTERATION OF YOUR TRANSMISSIONS OR CONTENT</li>
              </ul>
              <p className="text-white/80 leading-relaxed uppercase text-sm mt-4">
                OUR TOTAL LIABILITY TO YOU FOR ALL CLAIMS ARISING FROM OR RELATED TO THE SERVICE
                SHALL NOT EXCEED THE GREATER OF (A) THE AMOUNT YOU PAID US IN THE TWELVE (12) MONTHS
                PRECEDING THE CLAIM, OR (B) ONE HUNDRED U.S. DOLLARS ($100).
              </p>
            </section>

            {/* Indemnification */}
            <section>
              <h2 className="text-2xl font-semibold text-white mb-4">Indemnification</h2>
              <p className="text-white/80 leading-relaxed">
                You agree to indemnify, defend, and hold harmless AuthorFlow Studios, Rohimaya Publishing,
                Pagade Ventures, LLC, and their officers, directors, employees, agents, and affiliates
                from and against any claims, liabilities, damages, losses, costs, or expenses (including
                reasonable attorneys&apos; fees) arising out of or related to:
              </p>
              <ul className="list-disc list-inside text-white/80 space-y-2 mt-2">
                <li>Your use of the Service</li>
                <li>Your User Content</li>
                <li>Your violation of these Terms</li>
                <li>Your violation of any rights of another person or entity</li>
              </ul>
            </section>

            {/* Governing Law */}
            <section>
              <h2 className="text-2xl font-semibold text-white mb-4">Governing Law and Jurisdiction</h2>
              <p className="text-white/80 leading-relaxed">
                These Terms shall be governed by and construed in accordance with the laws of the
                State of Colorado, United States, without regard to its conflict of law provisions.
                Any legal action or proceeding arising out of or related to these Terms or the Service
                shall be brought exclusively in the state or federal courts located in Colorado, and
                you consent to the personal jurisdiction and venue of such courts.
              </p>
            </section>

            {/* Dispute Resolution */}
            <section>
              <h2 className="text-2xl font-semibold text-white mb-4">Dispute Resolution</h2>
              <p className="text-white/80 leading-relaxed">
                Before filing any legal claim, you agree to attempt to resolve disputes informally by
                contacting us at{' '}
                <a
                  href="mailto:support@authorflowstudios.rohimayapublishing.com"
                  className="text-af-lavender hover:text-white underline"
                >
                  support@authorflowstudios.rohimayapublishing.com
                </a>
                . We will attempt to resolve the dispute within 30 days. If the dispute is not resolved
                within 30 days, either party may proceed with legal remedies.
              </p>
            </section>

            {/* Termination */}
            <section>
              <h2 className="text-2xl font-semibold text-white mb-4">Termination</h2>
              <p className="text-white/80 leading-relaxed">
                We may terminate or suspend your account and access to the Service immediately, without
                prior notice or liability, for any reason, including if you breach these Terms. Upon
                termination:
              </p>
              <ul className="list-disc list-inside text-white/80 space-y-2 mt-2">
                <li>Your right to use the Service will immediately cease</li>
                <li>You may lose access to your content and generated files</li>
                <li>Any outstanding payment obligations remain due</li>
                <li>Provisions that by their nature should survive termination will survive</li>
              </ul>
              <p className="text-white/80 leading-relaxed mt-4">
                You may terminate your account at any time by contacting support or through your
                account settings.
              </p>
            </section>

            {/* Changes to Terms */}
            <section>
              <h2 className="text-2xl font-semibold text-white mb-4">Changes to These Terms</h2>
              <p className="text-white/80 leading-relaxed">
                We reserve the right to modify these Terms at any time. We will notify you of material
                changes by posting the updated Terms on this page with a new &quot;Last updated&quot; date.
                Your continued use of the Service after any changes constitutes acceptance of the new Terms.
                We encourage you to review these Terms periodically.
              </p>
            </section>

            {/* Severability */}
            <section>
              <h2 className="text-2xl font-semibold text-white mb-4">Severability</h2>
              <p className="text-white/80 leading-relaxed">
                If any provision of these Terms is held to be invalid, illegal, or unenforceable, the
                remaining provisions shall continue in full force and effect. The invalid provision
                shall be modified to the minimum extent necessary to make it valid and enforceable while
                preserving the parties&apos; original intent.
              </p>
            </section>

            {/* Entire Agreement */}
            <section>
              <h2 className="text-2xl font-semibold text-white mb-4">Entire Agreement</h2>
              <p className="text-white/80 leading-relaxed">
                These Terms, together with our Privacy Policy and any other policies referenced herein,
                constitute the entire agreement between you and AuthorFlow Studios regarding the Service
                and supersede all prior agreements, understandings, and communications.
              </p>
            </section>

            {/* Contact Information */}
            <section>
              <h2 className="text-2xl font-semibold text-white mb-4">Contact Us</h2>
              <p className="text-white/80 leading-relaxed">
                If you have any questions about these Terms, please contact us:
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
