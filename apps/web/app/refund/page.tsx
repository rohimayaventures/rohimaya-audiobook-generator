import Link from 'next/link'
import { Footer } from '@/components/layout'

/**
 * Refund Policy Page - AuthorFlow Studios
 * Production-ready refund policy for Colorado, USA jurisdiction
 */
export default function RefundPage() {
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
          <h1 className="text-4xl font-bold text-white mb-4">Refund Policy</h1>
          <p className="text-white/60 mb-8">Last updated: November 27, 2025</p>

          <div className="prose prose-invert prose-lg max-w-none space-y-8">
            {/* Introduction */}
            <section>
              <h2 className="text-2xl font-semibold text-white mb-4">Our Commitment</h2>
              <p className="text-white/80 leading-relaxed">
                At AuthorFlow Studios (&quot;we,&quot; &quot;our,&quot; or &quot;us&quot;), a product of Rohimaya Publishing,
                a division of Pagade Ventures, LLC, we are committed to providing high-quality AI-powered audiobook
                generation services. We understand that circumstances may arise where you need to request a refund,
                and we have designed this policy to be fair to both our customers and our business.
              </p>
            </section>

            {/* Free Trial */}
            <section>
              <h2 className="text-2xl font-semibold text-white mb-4">Free Trial</h2>
              <p className="text-white/80 leading-relaxed">
                We offer a free trial period for new users to evaluate our Service before committing to a paid
                subscription. During the trial:
              </p>
              <ul className="list-disc list-inside text-white/80 space-y-2 mt-2">
                <li>You can explore the platform and its features</li>
                <li>No payment information is required to start the trial</li>
                <li>Trial limitations may apply to word count and features</li>
                <li>You will not be charged unless you choose to upgrade</li>
              </ul>
              <p className="text-white/80 leading-relaxed mt-4">
                We encourage you to make full use of the free trial to ensure our Service meets your needs
                before purchasing a subscription.
              </p>
            </section>

            {/* Subscription Refunds */}
            <section>
              <h2 className="text-2xl font-semibold text-white mb-4">Subscription Refund Policy</h2>

              <h3 className="text-xl font-medium text-white mb-3">Within 7 Days of Purchase</h3>
              <p className="text-white/80 leading-relaxed">
                If you are not satisfied with your subscription, you may request a full refund within 7 days
                of your initial purchase, provided that:
              </p>
              <ul className="list-disc list-inside text-white/80 space-y-2 mt-2">
                <li>You have not generated more than 10,000 words of audio content</li>
                <li>You have not downloaded more than 3 complete audiobook chapters</li>
                <li>This is your first subscription with AuthorFlow Studios</li>
                <li>The refund request is submitted through our official support channel</li>
              </ul>

              <h3 className="text-xl font-medium text-white mb-3 mt-6">After 7 Days</h3>
              <p className="text-white/80 leading-relaxed">
                After the 7-day period, subscription fees are generally non-refundable. However, we may consider
                refund requests on a case-by-case basis for:
              </p>
              <ul className="list-disc list-inside text-white/80 space-y-2 mt-2">
                <li>Technical issues preventing use of the Service that we cannot resolve</li>
                <li>Billing errors or duplicate charges</li>
                <li>Extended service outages (more than 48 consecutive hours)</li>
                <li>Documented failure to deliver advertised features</li>
              </ul>
            </section>

            {/* Subscription Cancellation */}
            <section>
              <h2 className="text-2xl font-semibold text-white mb-4">Subscription Cancellation</h2>
              <p className="text-white/80 leading-relaxed">
                You may cancel your subscription at any time through your account settings or by contacting
                our support team:
              </p>
              <ul className="list-disc list-inside text-white/80 space-y-2 mt-2">
                <li>
                  <strong className="text-white">Effective Date:</strong> Cancellation takes effect at the end
                  of your current billing period
                </li>
                <li>
                  <strong className="text-white">Access:</strong> You retain full access to paid features until
                  your billing period ends
                </li>
                <li>
                  <strong className="text-white">No Partial Refunds:</strong> We do not provide prorated refunds
                  for unused portions of your billing period
                </li>
                <li>
                  <strong className="text-white">Data Retention:</strong> Your projects and generated audio files
                  remain accessible for 30 days after cancellation
                </li>
              </ul>
            </section>

            {/* Non-Refundable Items */}
            <section>
              <h2 className="text-2xl font-semibold text-white mb-4">Non-Refundable Items</h2>
              <p className="text-white/80 leading-relaxed">
                The following are not eligible for refunds:
              </p>
              <ul className="list-disc list-inside text-white/80 space-y-2 mt-2">
                <li>Subscription fees after the 7-day refund window (except as noted above)</li>
                <li>Usage-based charges for audio generation beyond plan limits</li>
                <li>Add-on purchases such as additional storage or premium voices</li>
                <li>Accounts terminated for Terms of Service violations</li>
                <li>Refund requests made more than 90 days after the original charge</li>
              </ul>
            </section>

            {/* How to Request a Refund */}
            <section>
              <h2 className="text-2xl font-semibold text-white mb-4">How to Request a Refund</h2>
              <p className="text-white/80 leading-relaxed">
                To request a refund, please follow these steps:
              </p>
              <ol className="list-decimal list-inside text-white/80 space-y-3 mt-4">
                <li>
                  <strong className="text-white">Email Us:</strong> Send a refund request to{' '}
                  <a
                    href="mailto:support@authorflowstudios.rohimayapublishing.com"
                    className="text-af-lavender hover:text-white underline"
                  >
                    support@authorflowstudios.rohimayapublishing.com
                  </a>
                </li>
                <li>
                  <strong className="text-white">Include Details:</strong> Your account email, subscription plan,
                  date of purchase, and reason for the refund request
                </li>
                <li>
                  <strong className="text-white">Wait for Review:</strong> We will review your request and respond
                  within 5 business days
                </li>
                <li>
                  <strong className="text-white">Refund Processing:</strong> Approved refunds are processed within
                  5-10 business days to your original payment method
                </li>
              </ol>
            </section>

            {/* Chargebacks */}
            <section>
              <h2 className="text-2xl font-semibold text-white mb-4">Chargebacks and Disputes</h2>
              <p className="text-white/80 leading-relaxed">
                We strongly encourage you to contact us directly before initiating a chargeback with your
                bank or credit card company. We are committed to resolving issues fairly and quickly.
              </p>
              <p className="text-white/80 leading-relaxed mt-4">
                If a chargeback is initiated without first contacting us, your account may be suspended pending
                resolution. Fraudulent chargebacks may result in permanent account termination and collection
                of owed amounts.
              </p>
            </section>

            {/* Changes to This Policy */}
            <section>
              <h2 className="text-2xl font-semibold text-white mb-4">Changes to This Policy</h2>
              <p className="text-white/80 leading-relaxed">
                We reserve the right to modify this Refund Policy at any time. Changes will be posted on this
                page with an updated &quot;Last updated&quot; date. Continued use of the Service after changes
                constitutes acceptance of the revised policy. Any refund requests will be processed according
                to the policy in effect at the time of your original purchase.
              </p>
            </section>

            {/* Contact Information */}
            <section>
              <h2 className="text-2xl font-semibold text-white mb-4">Contact Us</h2>
              <p className="text-white/80 leading-relaxed">
                For any questions about this Refund Policy or to submit a refund request:
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
                  <Link href="/cookies" className="text-af-lavender hover:text-white underline">
                    Cookie Policy
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
