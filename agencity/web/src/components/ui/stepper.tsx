'use client';

interface Step {
  id: number;
  name: string;
  description?: string;
}

interface StepperProps {
  steps: Step[];
  currentStep: number;
  onStepClick?: (step: number) => void;
}

export function Stepper({ steps, currentStep, onStepClick }: StepperProps) {
  return (
    <nav aria-label="Progress" className="mb-8">
      <ol className="flex items-center justify-between">
        {steps.map((step, index) => {
          const isCompleted = step.id < currentStep;
          const isCurrent = step.id === currentStep;

          return (
            <li key={step.id} className="relative flex-1">
              {index !== 0 && (
                <div
                  className={`absolute top-4 left-0 -translate-x-1/2 w-full h-0.5 ${
                    isCompleted ? 'bg-blue-600' : 'bg-gray-200'
                  }`}
                  style={{ width: 'calc(100% - 2rem)', marginLeft: '1rem' }}
                />
              )}
              <button
                onClick={() => onStepClick?.(step.id)}
                disabled={!isCompleted && !isCurrent}
                className={`
                  relative flex flex-col items-center group
                  ${onStepClick && (isCompleted || isCurrent) ? 'cursor-pointer' : 'cursor-default'}
                `}
              >
                <span
                  className={`
                    w-8 h-8 flex items-center justify-center rounded-full text-sm font-medium
                    transition-colors z-10
                    ${
                      isCompleted
                        ? 'bg-blue-600 text-white'
                        : isCurrent
                        ? 'border-2 border-blue-600 bg-white text-blue-600'
                        : 'border-2 border-gray-300 bg-white text-gray-500'
                    }
                  `}
                >
                  {isCompleted ? (
                    <svg
                      className="w-5 h-5"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                        clipRule="evenodd"
                      />
                    </svg>
                  ) : (
                    step.id
                  )}
                </span>
                <span
                  className={`
                    mt-2 text-xs font-medium
                    ${isCurrent ? 'text-blue-600' : 'text-gray-500'}
                  `}
                >
                  {step.name}
                </span>
              </button>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
