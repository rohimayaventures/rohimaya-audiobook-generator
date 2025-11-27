interface FeatureCardProps {
  icon: string
  title: string
  description: string
}

/**
 * FeatureCard - Used on landing page to highlight key features
 * Glassmorphism style with icon, title, and description
 */
export function FeatureCard({ icon, title, description }: FeatureCardProps) {
  return (
    <div className="glass p-6 hover:shadow-glow hover:border-af-purple-soft/30 transition-all duration-300 group">
      {/* Icon */}
      <div className="text-4xl mb-4 group-hover:scale-110 transition-transform duration-300">
        {icon}
      </div>

      {/* Title */}
      <h3 className="text-xl font-semibold text-white mb-2 group-hover:text-af-lavender transition-colors">
        {title}
      </h3>

      {/* Description */}
      <p className="text-white/60 text-sm leading-relaxed">
        {description}
      </p>
    </div>
  )
}

export default FeatureCard
