import Link from 'next/link';
import Image from 'next/image';

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-950 to-slate-900">
      {/* Header */}
      <header className="border-b border-slate-800">
        <div className="max-w-6xl mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <Image
              src="/hermes_logo.png"
              alt="Agencity"
              width={32}
              height={32}
              className="rounded-lg shadow-sm"
            />
            <span className="font-semibold text-xl text-white font-ivy-journal tracking-tight">Agencity</span>
          </div>
          <div className="flex items-center gap-4">
            <Link
              href="/dashboard"
              className="text-slate-400 hover:text-white transition-colors"
            >
              Dashboard
            </Link>
            <Link
              href="/onboarding"
              className="px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
            >
              Get Started
            </Link>
          </div>
        </div>
      </header>

      {/* Hero */}
      <main className="max-w-6xl mx-auto px-4 py-24">
        <div className="text-center">
          <div className="inline-block px-4 py-1.5 bg-blue-600/10 border border-blue-500/20 rounded-full text-blue-400 text-sm font-medium mb-6">
            Network Intelligence for Hiring
          </div>
          <h1 className="text-5xl md:text-6xl font-bold text-white mb-6 leading-tight">
            Hire through your network,<br />
            <span className="text-blue-400">not around it</span>
          </h1>
          <p className="text-xl text-slate-400 max-w-2xl mx-auto mb-10">
            Your next great hire is one introduction away. Agencity finds candidates in your network,
            shows you who can introduce you, and tells you when to reach out.
          </p>
          <div className="flex justify-center gap-4">
            <Link
              href="/onboarding"
              className="px-8 py-3 bg-blue-600 text-white rounded-lg font-medium text-lg hover:bg-blue-700 transition-colors"
            >
              Import Your Network
            </Link>
            <Link
              href="/dashboard"
              className="px-8 py-3 bg-slate-800 text-white rounded-lg font-medium text-lg hover:bg-slate-700 transition-colors border border-slate-700"
            >
              View Demo
            </Link>
          </div>
        </div>

        {/* Stats */}
        <div className="mt-20 grid md:grid-cols-3 gap-8 text-center">
          <div className="p-6">
            <div className="text-4xl font-bold text-white mb-2">10x</div>
            <div className="text-slate-400">higher response rate with warm intros</div>
          </div>
          <div className="p-6">
            <div className="text-4xl font-bold text-white mb-2">55%</div>
            <div className="text-slate-400">of your network matches roles you didn&apos;t know</div>
          </div>
          <div className="p-6">
            <div className="text-4xl font-bold text-white mb-2">2 min</div>
            <div className="text-slate-400">to find candidates in your network</div>
          </div>
        </div>

        {/* The Problem */}
        <div className="mt-32">
          <h2 className="text-3xl font-bold text-white text-center mb-6">
            Cold outreach is broken
          </h2>
          <p className="text-slate-400 text-center max-w-2xl mx-auto mb-12">
            You spend hours writing LinkedIn messages that get ignored. Recruiters charge $30k+ per hire.
            Meanwhile, your network already knows the perfect candidates — you just can&apos;t search it.
          </p>
        </div>

        {/* Features - The Four Pillars */}
        <div className="mt-16 grid md:grid-cols-2 gap-8">
          <div className="bg-slate-800/50 rounded-2xl p-8 border border-slate-700">
            <div className="w-12 h-12 bg-blue-600/20 rounded-xl flex items-center justify-center mb-6">
              <svg className="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-white mb-3">
              Tiered Search Results
            </h3>
            <p className="text-slate-400 mb-4">
              See candidates organized by warmth: direct connections first, then people one intro away,
              then recruiters who specialize in the role, then cold candidates.
            </p>
            <div className="flex flex-wrap gap-2">
              <span className="px-3 py-1 bg-green-600/20 text-green-400 rounded-full text-sm">Tier 1: Direct</span>
              <span className="px-3 py-1 bg-yellow-600/20 text-yellow-400 rounded-full text-sm">Tier 2: Warm Intro</span>
              <span className="px-3 py-1 bg-purple-600/20 text-purple-400 rounded-full text-sm">Tier 3: Recruiters</span>
              <span className="px-3 py-1 bg-slate-600/20 text-slate-400 rounded-full text-sm">Tier 4: Cold</span>
            </div>
          </div>

          <div className="bg-slate-800/50 rounded-2xl p-8 border border-slate-700">
            <div className="w-12 h-12 bg-orange-600/20 rounded-xl flex items-center justify-center mb-6">
              <svg className="w-6 h-6 text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-white mb-3">
              Timing Intelligence
            </h3>
            <p className="text-slate-400 mb-4">
              Know when to reach out. We track layoff announcements, long tenure patterns,
              and career signals so you contact people at the right moment.
            </p>
            <div className="flex flex-wrap gap-2">
              <span className="px-3 py-1 bg-red-600/20 text-red-400 rounded-full text-sm">Layoff Alerts</span>
              <span className="px-3 py-1 bg-yellow-600/20 text-yellow-400 rounded-full text-sm">Tenure Signals</span>
              <span className="px-3 py-1 bg-blue-600/20 text-blue-400 rounded-full text-sm">Ready to Move</span>
            </div>
          </div>

          <div className="bg-slate-800/50 rounded-2xl p-8 border border-slate-700">
            <div className="w-12 h-12 bg-green-600/20 rounded-xl flex items-center justify-center mb-6">
              <svg className="w-6 h-6 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-white mb-3">
              Network Activation
            </h3>
            <p className="text-slate-400 mb-4">
              Generate &quot;who would you recommend?&quot; messages for the right people in your network.
              Turn your connections into a sourcing engine.
            </p>
            <div className="bg-slate-900/50 rounded-lg p-4 mt-4 border border-slate-700">
              <p className="text-sm text-slate-300 italic">
                &quot;Hey Sarah, you&apos;ve worked with so many great engineers at Stripe.
                We&apos;re looking for a backend engineer — would you know anyone who might be a good fit?&quot;
              </p>
            </div>
          </div>

          <div className="bg-slate-800/50 rounded-2xl p-8 border border-slate-700">
            <div className="w-12 h-12 bg-purple-600/20 rounded-xl flex items-center justify-center mb-6">
              <svg className="w-6 h-6 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-white mb-3">
              Warm Path Finding
            </h3>
            <p className="text-slate-400 mb-4">
              For every candidate, see exactly how to reach them. Shared companies,
              mutual connections, alumni networks — we find the warmest path in.
            </p>
            <div className="flex items-center gap-2 mt-4">
              <div className="w-8 h-8 bg-slate-700 rounded-full flex items-center justify-center text-xs text-white">You</div>
              <div className="w-8 h-1 bg-gradient-to-r from-blue-500 to-purple-500 rounded"></div>
              <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-xs text-white">SC</div>
              <div className="w-8 h-1 bg-gradient-to-r from-purple-500 to-green-500 rounded"></div>
              <div className="w-8 h-8 bg-green-600 rounded-full flex items-center justify-center text-xs text-white">JD</div>
              <span className="text-sm text-slate-400 ml-2">Sarah → can intro → John</span>
            </div>
          </div>
        </div>

        {/* How it works */}
        <div className="mt-32">
          <h2 className="text-3xl font-bold text-white text-center mb-4">
            How it works
          </h2>
          <p className="text-slate-400 text-center mb-16">
            From LinkedIn export to candidate shortlist in minutes
          </p>
          <div className="grid md:grid-cols-4 gap-8">
            {[
              {
                step: 1,
                title: 'Import your network',
                description: 'Upload your LinkedIn connections CSV. We merge duplicates and enrich profiles.',
                icon: (
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                  </svg>
                ),
              },
              {
                step: 2,
                title: 'Add your roles',
                description: 'Tell us what positions you\'re hiring for. Skills, level, requirements.',
                icon: (
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                ),
              },
              {
                step: 3,
                title: 'Search candidates',
                description: 'Find matches ranked by warmth + fit. See who you know and who can intro.',
                icon: (
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                ),
              },
              {
                step: 4,
                title: 'Reach out warm',
                description: 'Use timing alerts + activation messages. Never send a cold email again.',
                icon: (
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                ),
              },
            ].map(({ step, title, description, icon }) => (
              <div key={step} className="text-center">
                <div className="w-14 h-14 bg-blue-600 text-white rounded-2xl flex items-center justify-center mx-auto mb-4">
                  {icon}
                </div>
                <div className="text-sm text-blue-400 font-medium mb-2">Step {step}</div>
                <h3 className="font-semibold text-white mb-2">{title}</h3>
                <p className="text-sm text-slate-400">{description}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Example / Social Proof */}
        <div className="mt-32 bg-slate-800/50 rounded-2xl p-8 md:p-12 border border-slate-700">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div>
              <div className="text-sm text-blue-400 font-medium mb-3">REAL EXAMPLE</div>
              <h3 className="text-2xl font-bold text-white mb-4">
                Confido found 81 candidates for Software Engineer
              </h3>
              <p className="text-slate-400 mb-6">
                With just 305 LinkedIn connections, Confido discovered 31 direct matches,
                24 people one intro away, and identified the best recruiters to help.
              </p>
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-green-600/20 rounded-lg flex items-center justify-center">
                    <span className="text-green-400 font-bold">31</span>
                  </div>
                  <span className="text-slate-300">Direct network matches</span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-yellow-600/20 rounded-lg flex items-center justify-center">
                    <span className="text-yellow-400 font-bold">24</span>
                  </div>
                  <span className="text-slate-300">Warm intro candidates</span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-purple-600/20 rounded-lg flex items-center justify-center">
                    <span className="text-purple-400 font-bold">1</span>
                  </div>
                  <span className="text-slate-300">Specialized recruiter</span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-slate-600/20 rounded-lg flex items-center justify-center">
                    <span className="text-slate-400 font-bold">25</span>
                  </div>
                  <span className="text-slate-300">Cold but qualified</span>
                </div>
              </div>
            </div>
            <div className="bg-slate-900 rounded-xl p-6 border border-slate-700">
              <div className="text-sm text-slate-400 mb-4">Search results preview</div>
              <div className="space-y-4">
                <div className="p-4 bg-slate-800 rounded-lg border-l-4 border-green-500">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="px-2 py-0.5 bg-green-600/20 text-green-400 rounded text-xs">Direct</span>
                    <span className="text-white font-medium">John Smith</span>
                  </div>
                  <div className="text-sm text-slate-400">Senior Engineer @ Google</div>
                  <div className="text-xs text-slate-500 mt-1">You connected at YC Demo Day</div>
                </div>
                <div className="p-4 bg-slate-800 rounded-lg border-l-4 border-yellow-500">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="px-2 py-0.5 bg-yellow-600/20 text-yellow-400 rounded text-xs">Warm Intro</span>
                    <span className="text-white font-medium">Jane Doe</span>
                  </div>
                  <div className="text-sm text-slate-400">Backend Engineer @ Stripe</div>
                  <div className="text-xs text-slate-500 mt-1">Sarah Chen worked with her (2019-2021)</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* CTA */}
        <div className="mt-32 text-center">
          <h2 className="text-3xl font-bold text-white mb-6">
            Ready to hire through your network?
          </h2>
          <p className="text-slate-400 max-w-xl mx-auto mb-8">
            Import your LinkedIn connections and find candidates you didn&apos;t know you could reach.
          </p>
          <Link
            href="/onboarding"
            className="inline-flex items-center gap-2 px-8 py-4 bg-blue-600 text-white rounded-lg font-medium text-lg hover:bg-blue-700 transition-colors"
          >
            Get Started — It&apos;s Free
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
            </svg>
          </Link>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800 mt-24">
        <div className="max-w-6xl mx-auto px-4 py-8 flex justify-between items-center">
          <div className="text-slate-500 text-sm">
            Agencity — Network Intelligence for Hiring
          </div>
          <div className="flex items-center gap-6 text-sm text-slate-500">
            <a href="#" className="hover:text-white transition-colors">About</a>
            <a href="#" className="hover:text-white transition-colors">Privacy</a>
            <a href="#" className="hover:text-white transition-colors">Terms</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
