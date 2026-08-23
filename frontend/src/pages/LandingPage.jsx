import { Link } from 'react-router-dom'
import { FEATURES } from '../constants/features'
import FeatureCard from '../components/ui/FeatureCard'
import FeatureIcon from '../components/ui/FeatureIcon'
import Disclaimer from '../components/layout/Disclaimer'

const STEPS = [
  { num: '1', title: 'Upload your PDF', desc: 'Drop your rental agreement—ClauseGuard accepts any standard PDF up to 20 MB.' },
  { num: '2', title: 'Process the document', desc: 'We extract every clause and build a searchable index in under a minute.' },
  { num: '3', title: 'Review & ask questions', desc: 'Run analysis tools and chat with your agreement before you sign.' },
]

export default function LandingPage() {
  return (
    <div className="page-bg">
      <header className="glass-nav">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center shadow-sm">
              <FeatureIcon name="shield" className="w-5 h-5 text-white" />
            </div>
            <span className="text-lg font-bold text-slate-900">
              Clause<span className="text-indigo-600">Guard</span>
            </span>
          </div>
          <div className="flex gap-2">
            <Link to="/login" className="text-sm font-medium text-slate-600 hover:text-slate-900 px-3 py-2 rounded-xl hover:bg-slate-100 transition-colors">
              Sign in
            </Link>
            <Link to="/register" className="btn-primary !py-2 !px-4 text-sm">
              Get started
            </Link>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="max-w-4xl mx-auto px-4 sm:px-6 pt-16 sm:pt-24 pb-12 text-center animate-slide-up">
        <div className="inline-flex items-center gap-2 rounded-full bg-indigo-50 border border-indigo-100 px-4 py-1.5 text-xs font-medium text-indigo-700 mb-6">
          <FeatureIcon name="shield" className="w-4 h-4" />
          AI-powered rental agreement review
        </div>
        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-slate-900 leading-tight tracking-tight">
          Understand what you&apos;re{' '}
          <span className="gradient-text">signing</span>
        </h1>
        <p className="mt-5 text-lg sm:text-xl text-slate-600 max-w-2xl mx-auto leading-relaxed">
          Upload your rental agreement and ClauseGuard extracts every clause, flags items worth your attention,
          and answers your questions—in plain language, before you sign.
        </p>
        <div className="mt-8 flex flex-col sm:flex-row gap-3 justify-center">
          <Link to="/register" className="btn-primary px-8 py-3.5 text-base">
            Analyse my agreement — free
          </Link>
          <Link to="/login" className="btn-secondary px-8 py-3.5 text-base">
            Sign in
          </Link>
        </div>

        {/* Trust strip */}
        <div className="mt-12 grid grid-cols-3 gap-4 max-w-lg mx-auto">
          {[
            { value: '5', label: 'Analysis tools' },
            { value: 'PDF', label: 'Upload format' },
            { value: 'Free', label: 'To get started' },
          ].map((item) => (
            <div key={item.label} className="rounded-2xl bg-white/70 border border-slate-200/80 px-3 py-3 shadow-sm">
              <p className="text-xl font-bold text-indigo-600">{item.value}</p>
              <p className="text-xs text-slate-500 mt-0.5">{item.label}</p>
            </div>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section className="max-w-5xl mx-auto px-4 sm:px-6 pb-14">
        <h2 className="text-center text-2xl font-bold text-slate-900 mb-2">How it works</h2>
        <p className="text-center text-slate-500 text-sm mb-8 max-w-md mx-auto">
          Three simple steps from upload to a fully analysed agreement.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {STEPS.map((step) => (
            <div key={step.num} className="relative rounded-2xl bg-white border border-slate-200 p-6 shadow-sm card-hover">
              <div className="w-10 h-10 rounded-full bg-indigo-600 text-white flex items-center justify-center font-bold text-sm mb-4">
                {step.num}
              </div>
              <h3 className="font-semibold text-slate-900">{step.title}</h3>
              <p className="mt-2 text-sm text-slate-500 leading-relaxed">{step.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="max-w-5xl mx-auto px-4 sm:px-6 pb-16">
        <h2 className="text-center text-2xl font-bold text-slate-900 mb-2">Everything you need to review a lease</h2>
        <p className="text-center text-slate-500 text-sm mb-8 max-w-lg mx-auto">
          Each tool focuses on one job—so you always know what you&apos;re looking at and why it matters.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {FEATURES.map((f) => (
            <FeatureCard key={f.id} feature={f} />
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="max-w-3xl mx-auto px-4 sm:px-6 pb-16">
        <div className="rounded-3xl bg-gradient-to-br from-indigo-600 via-violet-600 to-indigo-700 p-8 sm:p-10 text-center text-white shadow-soft">
          <h2 className="text-2xl font-bold">Ready to read your agreement with confidence?</h2>
          <p className="mt-2 text-indigo-100 text-sm max-w-md mx-auto">
            Create a free account, upload your PDF, and run your first analysis in minutes.
          </p>
          <Link to="/register" className="mt-6 inline-flex rounded-xl bg-white text-indigo-700 px-8 py-3 text-sm font-semibold hover:bg-indigo-50 transition-colors shadow-sm">
            Get started for free
          </Link>
        </div>
      </section>

      <footer className="border-t border-slate-200/80 py-8 text-center px-4 bg-white/50">
        <Disclaimer />
      </footer>
    </div>
  )
}
