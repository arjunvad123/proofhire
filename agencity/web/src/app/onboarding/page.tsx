'use client';

import { useState } from 'react';
import { Stepper } from '@/components/ui/stepper';
import { OnboardingProvider, useOnboarding } from '@/lib/onboarding-context';
import { CompanyInfoStep } from './steps/company-info';
import { UMOStep } from './steps/umo';
import { RolesStep } from './steps/roles';
import { LinkedInImportStep } from './steps/linkedin-import';
import { DatabaseImportStep } from './steps/database-import';
import { CompleteStep } from './steps/complete';

const STEPS = [
  { id: 1, name: 'Company Info' },
  { id: 2, name: 'What You Need' },
  { id: 3, name: 'Roles' },
  { id: 4, name: 'Your Network' },
  { id: 5, name: 'Your Database' },
  { id: 6, name: 'Complete' },
];

function OnboardingContent() {
  const { state, setCurrentStep } = useOnboarding();
  const [localStep, setLocalStep] = useState(state.currentStep);

  const handleNext = () => {
    const nextStep = localStep + 1;
    setLocalStep(nextStep);
    setCurrentStep(nextStep);
  };

  const handleBack = () => {
    const prevStep = localStep - 1;
    setLocalStep(prevStep);
    setCurrentStep(prevStep);
  };

  const handleSkip = () => {
    handleNext();
  };

  const renderStep = () => {
    switch (localStep) {
      case 1:
        return <CompanyInfoStep onNext={handleNext} />;
      case 2:
        return <UMOStep onNext={handleNext} onBack={handleBack} />;
      case 3:
        return <RolesStep onNext={handleNext} onBack={handleBack} onSkip={handleSkip} />;
      case 4:
        return <LinkedInImportStep onNext={handleNext} onBack={handleBack} onSkip={handleSkip} />;
      case 5:
        return <DatabaseImportStep onNext={handleNext} onBack={handleBack} onSkip={handleSkip} />;
      case 6:
        return <CompleteStep />;
      default:
        return <CompanyInfoStep onNext={handleNext} />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-3xl mx-auto px-4 py-12">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">
            Welcome to Agencity
          </h1>
          <p className="mt-2 text-gray-600">
            Let&apos;s set up your hiring network in a few steps
          </p>
        </div>

        {/* Stepper */}
        <Stepper steps={STEPS} currentStep={localStep} />

        {/* Step Content */}
        <div className="bg-white shadow-sm rounded-xl p-8">
          {renderStep()}
        </div>
      </div>
    </div>
  );
}

export default function OnboardingPage() {
  return (
    <OnboardingProvider>
      <OnboardingContent />
    </OnboardingProvider>
  );
}
