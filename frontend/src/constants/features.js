/** Shared copy + styling for product features shown across the UI. */
export const FEATURES = [
  {
    id: 'extract',
    title: 'Clause Extraction',
    shortDesc: 'Turns your PDF into numbered, searchable clauses automatically.',
    desc: 'Upload a rental agreement and ClauseGuard reads every page, splits the text into individual clauses, and stores them ready for analysis.',
    color: 'blue',
    step: 1,
  },
  {
    id: 'attention',
    title: 'Attention Review',
    shortDesc: 'Highlights clauses that match common rental red-flag patterns.',
    desc: 'Scans your agreement against predefined categories—like notice periods, deposits, and maintenance—and flags areas worth a closer read before you sign.',
    color: 'indigo',
    step: 2,
  },
  {
    id: 'missing',
    title: 'Missing Information',
    shortDesc: 'Checks whether key details like rent, dates, and parties are clearly stated.',
    desc: 'Looks for essential agreement details and tells you what was found, what is unclear, and what could not be located in the document.',
    color: 'teal',
    step: 3,
  },
  {
    id: 'search',
    title: 'Semantic Search',
    shortDesc: 'Find relevant clauses by meaning—not just exact keywords.',
    desc: 'Type a question or topic and ClauseGuard retrieves the most relevant clauses from your agreement using AI-powered semantic matching.',
    color: 'violet',
    step: 4,
  },
  {
    id: 'chat',
    title: 'Agreement Assistant',
    shortDesc: 'Ask plain-language questions and get answers grounded in your document.',
    desc: 'Chat with your uploaded agreement. Every answer cites the specific clauses it came from so you can verify the source yourself.',
    color: 'sky',
    step: 5,
  },
]

export const COLOR_MAP = {
  blue: {
    icon: 'bg-blue-100 text-blue-600',
    border: 'border-blue-200',
    accent: 'from-blue-500/10 to-blue-600/5',
    badge: 'bg-blue-50 text-blue-700',
    button: 'bg-blue-600 hover:bg-blue-700',
  },
  indigo: {
    icon: 'bg-indigo-100 text-indigo-600',
    border: 'border-indigo-200',
    accent: 'from-indigo-500/10 to-indigo-600/5',
    badge: 'bg-indigo-50 text-indigo-700',
    button: 'bg-indigo-600 hover:bg-indigo-700',
  },
  teal: {
    icon: 'bg-teal-100 text-teal-600',
    border: 'border-teal-200',
    accent: 'from-teal-500/10 to-teal-600/5',
    badge: 'bg-teal-50 text-teal-700',
    button: 'bg-teal-600 hover:bg-teal-700',
  },
  violet: {
    icon: 'bg-violet-100 text-violet-600',
    border: 'border-violet-200',
    accent: 'from-violet-500/10 to-violet-600/5',
    badge: 'bg-violet-50 text-violet-700',
    button: 'bg-violet-600 hover:bg-violet-700',
  },
  sky: {
    icon: 'bg-sky-100 text-sky-600',
    border: 'border-sky-200',
    accent: 'from-sky-500/10 to-sky-600/5',
    badge: 'bg-sky-50 text-sky-700',
    button: 'bg-sky-600 hover:bg-sky-700',
  },
}

export function getFeature(id) {
  return FEATURES.find((f) => f.id === id)
}
