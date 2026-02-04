import Link from 'next/link';

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      {/* Header */}
      <header className="border-b bg-white/80 backdrop-blur-sm fixed top-0 w-full z-50">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="font-bold text-xl">ProofHire</div>
          <nav className="flex items-center gap-6">
            <Link href="/login" className="text-sm text-slate-600 hover:text-slate-900">
              Log in
            </Link>
            <Link
              href="/signup"
              className="text-sm bg-slate-900 text-white px-4 py-2 rounded-md hover:bg-slate-800"
            >
              Get Started
            </Link>
          </nav>
        </div>
      </header>

      {/* Hero */}
      <section className="pt-32 pb-20 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-5xl font-bold tracking-tight text-slate-900 mb-6">
            Hire engineers based on
            <br />
            <span className="text-blue-600">proven work</span>, not resumes
          </h1>
          <p className="text-xl text-slate-600 mb-8 max-w-2xl mx-auto">
            ProofHire replaces resume screening with standardized work simulations.
            Get evidence-backed candidate briefs that show what engineers can actually do.
          </p>
          <div className="flex gap-4 justify-center">
            <Link
              href="/signup"
              className="bg-slate-900 text-white px-6 py-3 rounded-lg text-lg font-medium hover:bg-slate-800"
            >
              Start Hiring Better
            </Link>
            <Link
              href="/how-it-works"
              className="border border-slate-300 text-slate-700 px-6 py-3 rounded-lg text-lg font-medium hover:bg-slate-50"
            >
              See How It Works
            </Link>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-20 bg-white border-t">
        <div className="max-w-6xl mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-12">How ProofHire Works</h2>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl font-bold text-blue-600">1</span>
              </div>
              <h3 className="font-semibold text-lg mb-2">Define Your Role</h3>
              <p className="text-slate-600">
                Answer questions about your company and role. We generate a tailored
                evaluation rubric based on what you actually need.
              </p>
            </div>
            <div className="text-center">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl font-bold text-blue-600">2</span>
              </div>
              <h3 className="font-semibold text-lg mb-2">Candidates Complete Simulation</h3>
              <p className="text-slate-600">
                Candidates complete a realistic work simulation. They fix bugs, write tests,
                and explain their approach - just like real work.
              </p>
            </div>
            <div className="text-center">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl font-bold text-blue-600">3</span>
              </div>
              <h3 className="font-semibold text-lg mb-2">Review Evidence-Based Briefs</h3>
              <p className="text-slate-600">
                Get structured briefs showing what was proven and what needs interview follow-up.
                Every claim links to actual evidence.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Key Benefits */}
      <section className="py-20 border-t">
        <div className="max-w-6xl mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-12">Why ProofHire?</h2>
          <div className="grid md:grid-cols-2 gap-8">
            <div className="p-6 rounded-lg border bg-white">
              <h3 className="font-semibold text-lg mb-2">Evidence Over Claims</h3>
              <p className="text-slate-600">
                Every assessment is backed by artifacts - diffs, test logs, coverage reports.
                No guessing about candidate abilities.
              </p>
            </div>
            <div className="p-6 rounded-lg border bg-white">
              <h3 className="font-semibold text-lg mb-2">Fail-Closed Guarantee</h3>
              <p className="text-slate-600">
                If we can't prove something, we tell you. Unproven claims become
                targeted interview questions, not hidden gaps.
              </p>
            </div>
            <div className="p-6 rounded-lg border bg-white">
              <h3 className="font-semibold text-lg mb-2">Deterministic Grading</h3>
              <p className="text-slate-600">
                Tests either pass or fail. Code coverage is measurable. No subjective
                assessments where bias can creep in.
              </p>
            </div>
            <div className="p-6 rounded-lg border bg-white">
              <h3 className="font-semibold text-lg mb-2">Decision Support, Not Automation</h3>
              <p className="text-slate-600">
                We provide evidence and structure. You make the hiring decision.
                No black-box recommendations.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 bg-slate-900 text-white">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold mb-4">Ready to hire based on proof?</h2>
          <p className="text-slate-300 mb-8">
            Start evaluating candidates in minutes. No credit card required.
          </p>
          <Link
            href="/signup"
            className="bg-white text-slate-900 px-6 py-3 rounded-lg text-lg font-medium hover:bg-slate-100 inline-block"
          >
            Get Started Free
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t py-8">
        <div className="max-w-6xl mx-auto px-4 flex items-center justify-between">
          <div className="text-sm text-slate-500">
            ProofHire - Evidence-Based Engineering Hiring
          </div>
          <div className="flex gap-6 text-sm text-slate-500">
            <Link href="/privacy" className="hover:text-slate-700">Privacy</Link>
            <Link href="/terms" className="hover:text-slate-700">Terms</Link>
            <Link href="/contact" className="hover:text-slate-700">Contact</Link>
          </div>
        </div>
      </footer>
    </main>
  );
}
