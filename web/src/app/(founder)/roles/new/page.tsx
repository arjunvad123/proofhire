'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { createRole, getCurrentOrg } from '@/lib/api';

// Role Spec Interview Questions
const INTERVIEW_QUESTIONS = [
  {
    id: 'pace',
    question: 'How would you describe your engineering team\'s pace?',
    type: 'choice' as const,
    options: [
      'High - Ship fast, iterate quickly, comfortable with some tech debt',
      'Medium - Balance speed and quality, regular refactoring',
      'Low - Quality over speed, thorough reviews, minimal tech debt',
    ],
  },
  {
    id: 'quality_bar',
    question: 'What\'s your quality bar for production code?',
    type: 'choice' as const,
    options: [
      'High - Comprehensive tests, high coverage, strict reviews',
      'Medium - Core path tests, reasonable coverage, good reviews',
      'Pragmatic - Tests for critical paths, flexible on coverage',
    ],
  },
  {
    id: 'ambiguity',
    question: 'How much ambiguity will this person face?',
    type: 'choice' as const,
    options: [
      'High - Often figuring out what to build, not just how',
      'Medium - Some ambiguity, but generally clear direction',
      'Low - Well-defined specs and requirements',
    ],
  },
  {
    id: 'priorities',
    question: 'What skills are most important for this role? (Select up to 3)',
    type: 'multiselect' as const,
    options: [
      'Debugging complex issues',
      'Writing clean, maintainable code',
      'Strong testing practices',
      'Fast shipping / time to value',
      'Clear communication',
      'System design',
    ],
  },
];

export default function NewRolePage() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [title, setTitle] = useState('Founding Backend Engineer');
  const [answers, setAnswers] = useState<Record<string, string | string[]>>({});
  const [loading, setLoading] = useState(false);
  const [orgId, setOrgId] = useState<string | null>(null);

  useEffect(() => {
    getCurrentOrg().then((result) => {
      if (result.data) {
        setOrgId(result.data.id);
      }
    });
  }, []);

  const currentQuestion = INTERVIEW_QUESTIONS[step];
  const isLastQuestion = step === INTERVIEW_QUESTIONS.length - 1;

  const handleAnswer = (value: string) => {
    if (currentQuestion.type === 'multiselect') {
      const current = (answers[currentQuestion.id] as string[]) || [];
      if (current.includes(value)) {
        setAnswers({
          ...answers,
          [currentQuestion.id]: current.filter((v) => v !== value),
        });
      } else if (current.length < 3) {
        setAnswers({
          ...answers,
          [currentQuestion.id]: [...current, value],
        });
      }
    } else {
      setAnswers({
        ...answers,
        [currentQuestion.id]: value,
      });
    }
  };

  const handleNext = async () => {
    if (isLastQuestion) {
      if (!orgId) {
        alert('Organization not found. Please try logging in again.');
        return;
      }
      setLoading(true);
      // Create the role
      const result = await createRole(orgId, {
        title,
        interview_answers: answers as Record<string, string>,
      });

      if (result.data) {
        router.push(`/roles/${result.data.id}`);
      } else if (result.error) {
        alert(result.error);
      }
      setLoading(false);
    } else {
      setStep(step + 1);
    }
  };

  const canProceed = currentQuestion.type === 'multiselect'
    ? ((answers[currentQuestion.id] as string[])?.length || 0) > 0
    : !!answers[currentQuestion.id];

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b">
        <div className="max-w-3xl mx-auto px-4 py-4">
          <h1 className="font-bold text-xl">Create New Role</h1>
        </div>
      </header>

      {/* Progress */}
      <div className="max-w-3xl mx-auto px-4 py-4">
        <div className="flex gap-2">
          {INTERVIEW_QUESTIONS.map((_, i) => (
            <div
              key={i}
              className={`flex-1 h-1 rounded-full ${
                i <= step ? 'bg-slate-900' : 'bg-slate-200'
              }`}
            />
          ))}
        </div>
        <div className="text-sm text-slate-500 mt-2">
          Question {step + 1} of {INTERVIEW_QUESTIONS.length}
        </div>
      </div>

      {/* Question */}
      <main className="max-w-3xl mx-auto px-4 py-8">
        <div className="bg-white rounded-lg border p-8">
          {step === 0 && (
            <div className="mb-8">
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Role Title
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full px-4 py-3 border rounded-lg text-lg"
                placeholder="e.g., Founding Backend Engineer"
              />
            </div>
          )}

          <h2 className="text-xl font-semibold mb-6">{currentQuestion.question}</h2>

          <div className="space-y-3">
            {currentQuestion.options?.map((option) => {
              const isSelected = currentQuestion.type === 'multiselect'
                ? (answers[currentQuestion.id] as string[])?.includes(option)
                : answers[currentQuestion.id] === option;

              return (
                <button
                  key={option}
                  onClick={() => handleAnswer(option)}
                  className={`w-full text-left p-4 rounded-lg border-2 transition-colors ${
                    isSelected
                      ? 'border-slate-900 bg-slate-50'
                      : 'border-slate-200 hover:border-slate-300'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div
                      className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${
                        isSelected ? 'border-slate-900 bg-slate-900' : 'border-slate-300'
                      }`}
                    >
                      {isSelected && (
                        <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                          <path
                            fillRule="evenodd"
                            d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                            clipRule="evenodd"
                          />
                        </svg>
                      )}
                    </div>
                    <span>{option}</span>
                  </div>
                </button>
              );
            })}
          </div>

          <div className="flex justify-between mt-8">
            <button
              onClick={() => setStep(Math.max(0, step - 1))}
              disabled={step === 0}
              className="px-6 py-2 text-slate-600 hover:text-slate-900 disabled:opacity-50"
            >
              Back
            </button>
            <button
              onClick={handleNext}
              disabled={!canProceed || loading}
              className="px-6 py-2 bg-slate-900 text-white rounded-lg hover:bg-slate-800 disabled:opacity-50"
            >
              {loading ? 'Creating...' : isLastQuestion ? 'Create Role' : 'Next'}
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
