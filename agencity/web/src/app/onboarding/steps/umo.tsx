'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { TagInput } from '@/components/ui/tag-input';
import { useOnboarding } from '@/lib/onboarding-context';
import { updateUMO } from '@/lib/api';

interface UMOStepProps {
  onNext: () => void;
  onBack: () => void;
}

const WORK_STYLES = [
  { value: 'remote', label: 'Remote-first' },
  { value: 'hybrid', label: 'Hybrid' },
  { value: 'in-office', label: 'In-office' },
  { value: 'flexible', label: 'Flexible' },
];

export function UMOStep({ onNext, onBack }: UMOStepProps) {
  const { state, setUMO } = useOnboarding();

  const [formData, setFormData] = useState({
    ideal_candidate_description: state.umo?.ideal_candidate_description || '',
    preferred_backgrounds: state.umo?.preferred_backgrounds || [],
    must_have_traits: state.umo?.must_have_traits || [],
    anti_patterns: state.umo?.anti_patterns || [],
    culture_values: state.umo?.culture_values || [],
    work_style: state.umo?.work_style || '',
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!state.companyId) {
      setError('Company not found. Please go back and try again.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const umo = await updateUMO(state.companyId, formData);
      setUMO(umo);
      onNext();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-900">
          What are you looking for?
        </h2>
        <p className="mt-1 text-sm text-gray-500">
          Describe your ideal candidate profile
        </p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          {error}
        </div>
      )}

      <Textarea
        label="Describe your ideal candidate"
        value={formData.ideal_candidate_description}
        onChange={(e) =>
          setFormData({
            ...formData,
            ideal_candidate_description: e.target.value,
          })
        }
        rows={4}
        placeholder="We're looking for engineers who thrive in ambiguity, have experience building 0-1 products, and are excited about AI..."
        helperText="Be specific about what makes someone a great fit"
      />

      <TagInput
        label="Preferred Backgrounds"
        value={formData.preferred_backgrounds}
        onChange={(tags) =>
          setFormData({ ...formData, preferred_backgrounds: tags })
        }
        placeholder="FAANG, Startup, Fintech..."
        helperText="Where have your best hires come from?"
      />

      <TagInput
        label="Must-Have Traits"
        value={formData.must_have_traits}
        onChange={(tags) =>
          setFormData({ ...formData, must_have_traits: tags })
        }
        placeholder="Self-starter, Strong communicator..."
        helperText="Non-negotiable qualities"
      />

      <TagInput
        label="What to Avoid"
        value={formData.anti_patterns}
        onChange={(tags) => setFormData({ ...formData, anti_patterns: tags })}
        placeholder="Job hopper, No side projects..."
        helperText="Red flags or dealbreakers"
      />

      <TagInput
        label="Culture Values"
        value={formData.culture_values}
        onChange={(tags) => setFormData({ ...formData, culture_values: tags })}
        placeholder="Move fast, Customer obsessed..."
      />

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Work Style
        </label>
        <select
          value={formData.work_style}
          onChange={(e) =>
            setFormData({ ...formData, work_style: e.target.value })
          }
          className="block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="">Select work style</option>
          {WORK_STYLES.map((style) => (
            <option key={style.value} value={style.value}>
              {style.label}
            </option>
          ))}
        </select>
      </div>

      <div className="flex justify-between pt-4">
        <Button type="button" variant="outline" onClick={onBack}>
          Back
        </Button>
        <Button type="submit" loading={loading}>
          Continue
        </Button>
      </div>
    </form>
  );
}
