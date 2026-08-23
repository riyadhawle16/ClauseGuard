import { COLOR_MAP } from '../../constants/features'
import FeatureIcon from './FeatureIcon'

export default function FeatureCard({ feature, compact = false }) {
  const colors = COLOR_MAP[feature.color] || COLOR_MAP.blue

  if (compact) {
    return (
      <div className={`card-hover rounded-2xl border ${colors.border} bg-white p-4 shadow-sm`}>
        <div className={`inline-flex rounded-xl p-2.5 ${colors.icon}`}>
          <FeatureIcon name={feature.id} />
        </div>
        <h3 className="mt-3 font-semibold text-slate-900">{feature.title}</h3>
        <p className="mt-1 text-sm leading-relaxed text-slate-500">{feature.shortDesc}</p>
      </div>
    )
  }

  return (
    <div className={`card-hover relative overflow-hidden rounded-2xl border ${colors.border} bg-white p-6 shadow-sm`}>
      <div className={`absolute inset-0 bg-gradient-to-br ${colors.accent} pointer-events-none`} />
      <div className="relative">
        <div className="flex items-start gap-4">
          <div className={`shrink-0 rounded-2xl p-3 ${colors.icon}`}>
            <FeatureIcon name={feature.id} className="w-6 h-6" />
          </div>
          <div>
            {feature.step != null && (
              <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${colors.badge}`}>
                Step {feature.step}
              </span>
            )}
            <h3 className="mt-1 text-lg font-semibold text-slate-900">{feature.title}</h3>
            <p className="mt-2 text-sm leading-relaxed text-slate-600">{feature.desc}</p>
          </div>
        </div>
      </div>
    </div>
  )
}
