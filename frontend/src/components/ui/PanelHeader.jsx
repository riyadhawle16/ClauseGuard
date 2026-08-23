import { COLOR_MAP, getFeature } from '../../constants/features'
import FeatureIcon from './FeatureIcon'

/** Consistent header for analysis panels with icon + 1–2 line description. */
export default function PanelHeader({ featureId, title, description, action }) {
  const feature = getFeature(featureId)
  const colors = COLOR_MAP[feature?.color || 'blue']

  return (
    <div className="px-5 py-4 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div className="flex items-start gap-3 min-w-0">
        <div className={`shrink-0 rounded-xl p-2.5 ${colors.icon}`}>
          <FeatureIcon name={featureId} />
        </div>
        <div className="min-w-0">
          <h2 className="text-base font-semibold text-slate-900">{title || feature?.title}</h2>
          <p className="text-sm text-slate-500 mt-0.5 leading-relaxed">
            {description || feature?.shortDesc}
          </p>
        </div>
      </div>
      {action && <div className="shrink-0">{action}</div>}
    </div>
  )
}
