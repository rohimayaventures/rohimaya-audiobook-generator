import Link from 'next/link'
import { Footer } from '@/components/layout'

/**
 * Cookie Policy Page - AuthorFlow Studios
 * Production-ready cookie policy for Colorado, USA jurisdiction
 */
export default function CookiesPage() {
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
          <h1 className="text-4xl font-bold text-white mb-4">Cookie Policy</h1>
          <p className="text-white/60 mb-8">Last updated: November 27, 2025</p>

          <div className="prose prose-invert prose-lg max-w-none space-y-8">
            {/* Introduction */}
            <section>
              <h2 className="text-2xl font-semibold text-white mb-4">What Are Cookies</h2>
              <p className="text-white/80 leading-relaxed">
                Cookies are small text files that are stored on your computer or mobile device when you visit
                a website. They are widely used to make websites work more efficiently, provide a better user
                experience, and give website owners information about how their site is being used.
              </p>
              <p className="text-white/80 leading-relaxed mt-4">
                This Cookie Policy explains how AuthorFlow Studios (&quot;we,&quot; &quot;our,&quot; or &quot;us&quot;),
                a product of Rohimaya Publishing, a division of Pagade Ventures, LLC, uses cookies and similar
                technologies on our website at authorflowstudios.rohimayapublishing.com (the &quot;Service&quot;).
              </p>
            </section>

            {/* Types of Cookies We Use */}
            <section>
              <h2 className="text-2xl font-semibold text-white mb-4">Types of Cookies We Use</h2>

              <h3 className="text-xl font-medium text-white mb-3">Essential Cookies</h3>
              <p className="text-white/80 leading-relaxed">
                These cookies are strictly necessary for the operation of our Service. They enable core
                functionality such as security, network management, and account access. You cannot opt out
                of these cookies as the Service would not function properly without them.
              </p>
              <div className="mt-3 p-4 bg-af-card/50 rounded-lg border border-af-card-border">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-white/90 text-left">
                      <th className="pb-2">Cookie Name</th>
                      <th className="pb-2">Purpose</th>
                      <th className="pb-2">Duration</th>
                    </tr>
                  </thead>
                  <tbody className="text-white/70">
                    <tr>
                      <td className="py-1">sb-*-auth-token</td>
                      <td className="py-1">Supabase authentication</td>
                      <td className="py-1">Session</td>
                    </tr>
                    <tr>
                      <td className="py-1">last_activity</td>
                      <td className="py-1">Session timeout tracking</td>
                      <td className="py-1">30 minutes</td>
                    </tr>
                    <tr>
                      <td className="py-1">__stripe_mid</td>
                      <td className="py-1">Stripe fraud prevention</td>
                      <td className="py-1">1 year</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <h3 className="text-xl font-medium text-white mb-3 mt-6">Functional Cookies</h3>
              <p className="text-white/80 leading-relaxed">
                These cookies enable enhanced functionality and personalization. They may be set by us or
                by third-party providers whose services we have added to our pages. If you disable these
                cookies, some or all of these services may not function properly.
              </p>
              <div className="mt-3 p-4 bg-af-card/50 rounded-lg border border-af-card-border">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-white/90 text-left">
                      <th className="pb-2">Cookie Name</th>
                      <th className="pb-2">Purpose</th>
                      <th className="pb-2">Duration</th>
                    </tr>
                  </thead>
                  <tbody className="text-white/70">
                    <tr>
                      <td className="py-1">theme_preference</td>
                      <td className="py-1">User interface preferences</td>
                      <td className="py-1">1 year</td>
                    </tr>
                    <tr>
                      <td className="py-1">voice_preference</td>
                      <td className="py-1">Last selected voice settings</td>
                      <td className="py-1">30 days</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <h3 className="text-xl font-medium text-white mb-3 mt-6">Analytics Cookies</h3>
              <p className="text-white/80 leading-relaxed">
                These cookies help us understand how visitors interact with our Service by collecting and
                reporting information anonymously. This helps us improve our Service and user experience.
              </p>
              <div className="mt-3 p-4 bg-af-card/50 rounded-lg border border-af-card-border">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-white/90 text-left">
                      <th className="pb-2">Cookie Name</th>
                      <th className="pb-2">Purpose</th>
                      <th className="pb-2">Duration</th>
                    </tr>
                  </thead>
                  <tbody className="text-white/70">
                    <tr>
                      <td className="py-1">_vercel_insights</td>
                      <td className="py-1">Vercel Analytics</td>
                      <td className="py-1">Session</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </section>

            {/* Third-Party Cookies */}
            <section>
              <h2 className="text-2xl font-semibold text-white mb-4">Third-Party Cookies</h2>
              <p className="text-white/80 leading-relaxed">
                In addition to our own cookies, we may also use various third-party cookies to report usage
                statistics of the Service and deliver services:
              </p>
              <ul className="list-disc list-inside text-white/80 space-y-2 mt-4">
                <li>
                  <strong className="text-white">Stripe:</strong> Payment processing and fraud prevention
                </li>
                <li>
                  <strong className="text-white">Supabase:</strong> Authentication and session management
                </li>
                <li>
                  <strong className="text-white">Google:</strong> OAuth authentication when signing in with Google
                </li>
                <li>
                  <strong className="text-white">Vercel:</strong> Performance analytics and edge functions
                </li>
              </ul>
              <p className="text-white/80 leading-relaxed mt-4">
                These third-party services have their own privacy policies addressing how they use such information.
              </p>
            </section>

            {/* Local Storage */}
            <section>
              <h2 className="text-2xl font-semibold text-white mb-4">Local Storage and Session Storage</h2>
              <p className="text-white/80 leading-relaxed">
                In addition to cookies, we use browser local storage and session storage to store certain
                information locally on your device. These technologies work similarly to cookies but can
                store larger amounts of data.
              </p>
              <ul className="list-disc list-inside text-white/80 space-y-2 mt-4">
                <li>
                  <strong className="text-white">Session Data:</strong> Temporary data to maintain your session state
                </li>
                <li>
                  <strong className="text-white">Draft Content:</strong> Auto-saved drafts of unsaved work
                </li>
                <li>
                  <strong className="text-white">UI State:</strong> Panel positions, collapsed sections, and view preferences
                </li>
              </ul>
            </section>

            {/* Managing Cookies */}
            <section>
              <h2 className="text-2xl font-semibold text-white mb-4">How to Manage Cookies</h2>
              <p className="text-white/80 leading-relaxed">
                Most web browsers allow you to control cookies through their settings. You can typically:
              </p>
              <ul className="list-disc list-inside text-white/80 space-y-2 mt-4">
                <li>View cookies stored on your computer</li>
                <li>Delete all or specific cookies</li>
                <li>Block all cookies or cookies from specific sites</li>
                <li>Block third-party cookies</li>
                <li>Clear all cookies when you close the browser</li>
                <li>Accept or reject cookies on a case-by-case basis</li>
              </ul>

              <h3 className="text-xl font-medium text-white mb-3 mt-6">Browser-Specific Instructions</h3>
              <p className="text-white/80 leading-relaxed">
                To learn how to manage cookies in your specific browser, please visit:
              </p>
              <ul className="list-disc list-inside text-white/80 space-y-2 mt-2">
                <li>
                  <a
                    href="https://support.google.com/chrome/answer/95647"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-af-lavender hover:text-white underline"
                  >
                    Google Chrome
                  </a>
                </li>
                <li>
                  <a
                    href="https://support.mozilla.org/en-US/kb/cookies-information-websites-store-on-your-computer"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-af-lavender hover:text-white underline"
                  >
                    Mozilla Firefox
                  </a>
                </li>
                <li>
                  <a
                    href="https://support.apple.com/guide/safari/manage-cookies-sfri11471/mac"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-af-lavender hover:text-white underline"
                  >
                    Apple Safari
                  </a>
                </li>
                <li>
                  <a
                    href="https://support.microsoft.com/en-us/microsoft-edge/delete-cookies-in-microsoft-edge-63947406-40ac-c3b8-57b9-2a946a29ae09"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-af-lavender hover:text-white underline"
                  >
                    Microsoft Edge
                  </a>
                </li>
              </ul>
            </section>

            {/* Impact of Disabling Cookies */}
            <section>
              <h2 className="text-2xl font-semibold text-white mb-4">Impact of Disabling Cookies</h2>
              <p className="text-white/80 leading-relaxed">
                Please note that if you choose to disable or delete cookies, some features of our Service
                may not function properly. Specifically:
              </p>
              <ul className="list-disc list-inside text-white/80 space-y-2 mt-4">
                <li>You may not be able to log in or maintain a session</li>
                <li>Your preferences may not be remembered</li>
                <li>Payment processing may be impacted</li>
                <li>Some interactive features may not work</li>
              </ul>
              <p className="text-white/80 leading-relaxed mt-4">
                Essential cookies cannot be disabled without significantly affecting the functionality of the Service.
              </p>
            </section>

            {/* Do Not Track */}
            <section>
              <h2 className="text-2xl font-semibold text-white mb-4">Do Not Track Signals</h2>
              <p className="text-white/80 leading-relaxed">
                Some browsers have a &quot;Do Not Track&quot; feature that signals to websites that you do not
                want to have your online activity tracked. We currently do not respond to Do Not Track signals.
                However, you can manage cookies as described above to limit tracking.
              </p>
            </section>

            {/* Updates to This Policy */}
            <section>
              <h2 className="text-2xl font-semibold text-white mb-4">Updates to This Cookie Policy</h2>
              <p className="text-white/80 leading-relaxed">
                We may update this Cookie Policy from time to time to reflect changes in our practices or
                for other operational, legal, or regulatory reasons. We will notify you of any material
                changes by posting the new Cookie Policy on this page with an updated &quot;Last updated&quot; date.
              </p>
            </section>

            {/* Contact Information */}
            <section>
              <h2 className="text-2xl font-semibold text-white mb-4">Contact Us</h2>
              <p className="text-white/80 leading-relaxed">
                If you have any questions about our use of cookies or this Cookie Policy:
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

            {/* Related Policies */}
            <section>
              <h2 className="text-2xl font-semibold text-white mb-4">Related Policies</h2>
              <p className="text-white/80 leading-relaxed">
                Please also review our other policies:
              </p>
              <ul className="list-disc list-inside text-white/80 space-y-2 mt-2">
                <li>
                  <Link href="/privacy" className="text-af-lavender hover:text-white underline">
                    Privacy Policy
                  </Link>
                </li>
                <li>
                  <Link href="/terms" className="text-af-lavender hover:text-white underline">
                    Terms of Use
                  </Link>
                </li>
                <li>
                  <Link href="/refund" className="text-af-lavender hover:text-white underline">
                    Refund Policy
                  </Link>
                </li>
              </ul>
            </section>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  )
}
