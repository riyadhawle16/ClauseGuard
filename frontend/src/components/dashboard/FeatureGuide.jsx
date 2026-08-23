import { FEATURES } from '../../constants/features'
import FeatureCard from '../ui/FeatureCard'

export default function FeatureGuide() {
  return (
    <section className="mb-8">
      <div className="mb-4">
        <h2 className="text-lg font-semibold text-slate-900">What ClauseGuard can do</h2>
        <p className="mt-1 text-sm text-slate-500">
          Upload an agreement, process it once, then use these tools to understand it before you sign.
        </p>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {FEATURES.map((feature) => (
          <FeatureCard key={feature.id} feature={feature} compact />
        ))}
      </div>
    </section>
  )
}
