import { NextRequest, NextResponse } from 'next/server'

/**
 * Contact Form API Route
 * Sends contact form submissions via Brevo API
 */

interface ContactFormData {
  name: string
  email: string
  subject: string
  message: string
}

export async function POST(request: NextRequest) {
  try {
    const body: ContactFormData = await request.json()

    // Validate required fields
    if (!body.name || !body.email || !body.subject || !body.message) {
      return NextResponse.json(
        { error: 'All fields are required' },
        { status: 400 }
      )
    }

    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(body.email)) {
      return NextResponse.json(
        { error: 'Invalid email address' },
        { status: 400 }
      )
    }

    const brevoApiKey = process.env.BREVO_API_KEY
    const contactEmail = process.env.CONTACT_EMAIL || 'support@rohimayapublishing.com'

    if (!brevoApiKey) {
      console.error('BREVO_API_KEY not configured')
      return NextResponse.json(
        { error: 'Email service not configured' },
        { status: 500 }
      )
    }

    // Send email via Brevo API
    const response = await fetch('https://api.brevo.com/v3/smtp/email', {
      method: 'POST',
      headers: {
        'accept': 'application/json',
        'api-key': brevoApiKey,
        'content-type': 'application/json',
      },
      body: JSON.stringify({
        sender: {
          name: 'AuthorFlow Studios',
          email: 'noreply@authorflowstudios.rohimayapublishing.com',
        },
        to: [
          {
            email: contactEmail,
            name: 'AuthorFlow Support',
          },
        ],
        replyTo: {
          email: body.email,
          name: body.name,
        },
        subject: `[Contact Form] ${body.subject}`,
        htmlContent: `
          <!DOCTYPE html>
          <html>
          <head>
            <meta charset="utf-8">
          </head>
          <body style="margin: 0; padding: 0; background: #0a0a1a; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
            <table width="100%" cellpadding="0" cellspacing="0" style="background: #0a0a1a; padding: 40px 20px;">
              <tr>
                <td align="center">
                  <table width="100%" style="max-width: 600px; background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 16px;">
                    <tr>
                      <td style="padding: 32px; border-bottom: 1px solid rgba(255, 255, 255, 0.1);">
                        <h1 style="margin: 0; font-family: Georgia, serif; font-size: 24px; color: #ffffff;">
                          New Contact Form Submission
                        </h1>
                      </td>
                    </tr>
                    <tr>
                      <td style="padding: 32px;">
                        <p style="margin: 0 0 16px; color: #c4b5fd; font-size: 14px; text-transform: uppercase; letter-spacing: 1px;">From</p>
                        <p style="margin: 0 0 24px; color: #ffffff; font-size: 16px;">
                          <strong>${body.name}</strong><br>
                          <a href="mailto:${body.email}" style="color: #a78bfa;">${body.email}</a>
                        </p>

                        <p style="margin: 0 0 16px; color: #c4b5fd; font-size: 14px; text-transform: uppercase; letter-spacing: 1px;">Subject</p>
                        <p style="margin: 0 0 24px; color: #ffffff; font-size: 16px;">${body.subject}</p>

                        <p style="margin: 0 0 16px; color: #c4b5fd; font-size: 14px; text-transform: uppercase; letter-spacing: 1px;">Message</p>
                        <p style="margin: 0; color: #ffffff; font-size: 16px; line-height: 1.6; white-space: pre-wrap;">${body.message}</p>
                      </td>
                    </tr>
                    <tr>
                      <td style="padding: 24px 32px; background: rgba(0,0,0,0.2); border-top: 1px solid rgba(255, 255, 255, 0.1);">
                        <p style="margin: 0; color: rgba(255, 255, 255, 0.4); font-size: 12px; text-align: center;">
                          Sent from AuthorFlow Studios Contact Form
                        </p>
                      </td>
                    </tr>
                  </table>
                </td>
              </tr>
            </table>
          </body>
          </html>
        `,
      }),
    })

    if (!response.ok) {
      const errorData = await response.json()
      console.error('Brevo API error:', errorData)
      return NextResponse.json(
        { error: 'Failed to send message' },
        { status: 500 }
      )
    }

    return NextResponse.json(
      { success: true, message: 'Message sent successfully' },
      { status: 200 }
    )
  } catch (error) {
    console.error('Contact form error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}
