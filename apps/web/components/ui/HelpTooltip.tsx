'use client'

import { useState } from 'react'
import { clsx } from 'clsx'

interface HelpTooltipProps {
  content: string
  title?: string
  children?: React.ReactNode
  position?: 'top' | 'bottom' | 'left' | 'right'
  className?: string
}

/**
 * HelpTooltip - Contextual help tooltip with (?) icon
 */
export function HelpTooltip({
  content,
  title,
  children,
  position = 'top',
  className,
}: HelpTooltipProps) {
  const [isVisible, setIsVisible] = useState(false)

  const positionClasses = {
    top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
    bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
    left: 'right-full top-1/2 -translate-y-1/2 mr-2',
    right: 'left-full top-1/2 -translate-y-1/2 ml-2',
  }

  const arrowClasses = {
    top: 'top-full left-1/2 -translate-x-1/2 border-t-white/20 border-x-transparent border-b-transparent',
    bottom: 'bottom-full left-1/2 -translate-x-1/2 border-b-white/20 border-x-transparent border-t-transparent',
    left: 'left-full top-1/2 -translate-y-1/2 border-l-white/20 border-y-transparent border-r-transparent',
    right: 'right-full top-1/2 -translate-y-1/2 border-r-white/20 border-y-transparent border-l-transparent',
  }

  return (
    <div className={clsx('relative inline-flex items-center', className)}>
      <button
        type="button"
        className="w-5 h-5 flex items-center justify-center rounded-full bg-white/10 hover:bg-white/20 text-white/60 hover:text-white transition-all text-xs font-medium"
        onMouseEnter={() => setIsVisible(true)}
        onMouseLeave={() => setIsVisible(false)}
        onFocus={() => setIsVisible(true)}
        onBlur={() => setIsVisible(false)}
        aria-label="Help"
      >
        ?
      </button>

      {isVisible && (
        <div
          className={clsx(
            'absolute z-50 w-64 p-3 rounded-lg',
            'bg-af-dark/95 backdrop-blur-xl border border-white/20',
            'shadow-xl shadow-black/20',
            'text-sm text-white/90',
            positionClasses[position]
          )}
          role="tooltip"
        >
          {title && (
            <div className="font-semibold text-white mb-1">{title}</div>
          )}
          <div className="text-white/70 leading-relaxed">{content}</div>
          {children}
          {/* Arrow */}
          <div
            className={clsx(
              'absolute w-0 h-0 border-4',
              arrowClasses[position]
            )}
          />
        </div>
      )}
    </div>
  )
}

/**
 * Pre-defined help content for common fields
 */
export const HELP_CONTENT = {
  audioFormat: {
    title: 'Audio Format',
    content: 'MP3: Most compatible, smaller files. M4B: Audiobook format with chapter markers. FLAC: Lossless quality, larger files. WAV: Uncompressed, professional editing.',
  },
  inputLanguage: {
    title: 'Input Language',
    content: 'Select the language your manuscript is written in. This helps the AI understand pronunciation and context.',
  },
  outputLanguage: {
    title: 'Output Language',
    content: 'If different from input, your text will be translated before generating audio. Great for reaching international audiences!',
  },
  voicePreset: {
    title: 'Voice Preset',
    content: 'Each narrator has a unique personality and style. Preview voices before selecting to find the perfect match for your book.',
  },
  emotionStyle: {
    title: 'Emotion Style',
    content: 'Add emotional direction like "warm and intimate", "dramatic and intense", or "calm and soothing" to customize the narration tone.',
  },
  findawayPackage: {
    title: 'Findaway Package',
    content: 'Findaway-ready packages include properly named files, chapter markers, and retail samples for easy distribution to 40+ audiobook platforms.',
  },
  retailSample: {
    title: 'Retail Sample',
    content: 'A 3-5 minute preview excerpt that potential listeners hear before purchasing. Our AI selects the most engaging passage from your book.',
  },
  chapterReview: {
    title: 'Chapter Review',
    content: 'Drag to reorder chapters, change segment types (front matter, body, back matter), or exclude chapters you don\'t want narrated.',
  },
}

/**
 * FormFieldWithHelp - Form label with integrated help tooltip
 */
export function FormFieldWithHelp({
  label,
  helpKey,
  required = false,
  children,
  className,
}: {
  label: string
  helpKey: keyof typeof HELP_CONTENT
  required?: boolean
  children: React.ReactNode
  className?: string
}) {
  const help = HELP_CONTENT[helpKey]

  return (
    <div className={className}>
      <div className="flex items-center gap-2 mb-2">
        <label className="text-sm font-medium text-white">
          {label}
          {required && <span className="text-red-400 ml-1">*</span>}
        </label>
        <HelpTooltip content={help.content} title={help.title} />
      </div>
      {children}
    </div>
  )
}

export default HelpTooltip
