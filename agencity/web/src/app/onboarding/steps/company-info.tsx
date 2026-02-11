'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { TagInput } from '@/components/ui/tag-input';
import { useOnboarding } from '@/lib/onboarding-context';
import { createCompany } from '@/lib/api';

interface CompanyInfoStepProps {
  onNext: () => void;
}

const STAGES = [
  { value: 'pre_seed', label: 'Pre-seed' },
  { value: 'seed', label: 'Seed' },
  { value: 'series_a', label: 'Series A' },
  { value: 'series_b', label: 'Series B' },
  { value: 'series_c_plus', label: 'Series C+' },
  { value: 'bootstrapped', label: 'Bootstrapped' },
  { value: 'public', label: 'Public' },
];

export function CompanyInfoStep({ onNext }: CompanyInfoStepProps) {
  const { state, setCompany } = useOnboarding();

  const [formData, setFormData] = useState({
    name: state.company?.name || '',
    domain: state.company?.domain || '',
    founder_name: state.company?.founder_name || '',
    founder_email: state.company?.founder_email || '',
    stage: state.company?.stage || '',
    industry: state.company?.industry || '',
    tech_stack: state.company?.tech_stack || [],
    team_size: state.company?.team_size?.toString() || '',
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const company = await createCompany({
        name: formData.name,
        founder_email: formData.founder_email,
        founder_name: formData.founder_name,
        domain: formData.domain || undefined,
        stage: formData.stage || undefined,
        industry: formData.industry || undefined,
        tech_stack: formData.tech_stack,
        team_size: formData.team_size ? parseInt(formData.team_size) : undefined,
      });

      setCompany(company);
      onNext();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create company');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-900">
          Tell us about your company
        </h2>
        <p className="mt-1 text-sm text-gray-500">
          This helps us find the right candidates for you
        </p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          {error}
        </div>
      )}

      <div className="grid grid-cols-2 gap-4">
        <Input
          label="Company Name *"
          value={formData.name}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          placeholder="Acme Inc"
          required
        />
        <Input
          label="Domain"
          value={formData.domain}
          onChange={(e) => setFormData({ ...formData, domain: e.target.value })}
          placeholder="acme.com"
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Input
          label="Your Name *"
          value={formData.founder_name}
          onChange={(e) =>
            setFormData({ ...formData, founder_name: e.target.value })
          }
          placeholder="John Doe"
          required
        />
        <Input
          label="Your Email *"
          type="email"
          value={formData.founder_email}
          onChange={(e) =>
            setFormData({ ...formData, founder_email: e.target.value })
          }
          placeholder="john@acme.com"
          required
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Stage
          </label>
          <select
            value={formData.stage}
            onChange={(e) => setFormData({ ...formData, stage: e.target.value })}
            className="block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">Select stage</option>
            {STAGES.map((stage) => (
              <option key={stage.value} value={stage.value}>
                {stage.label}
              </option>
            ))}
          </select>
        </div>
        <Input
          label="Industry"
          value={formData.industry}
          onChange={(e) =>
            setFormData({ ...formData, industry: e.target.value })
          }
          placeholder="Fintech, AI, etc."
        />
      </div>

      <TagInput
        label="Tech Stack"
        value={formData.tech_stack}
        onChange={(tags) => setFormData({ ...formData, tech_stack: tags })}
        placeholder="Python, TypeScript, React..."
        helperText="Press Enter to add each technology"
      />

      <Input
        label="Team Size"
        type="number"
        value={formData.team_size}
        onChange={(e) => setFormData({ ...formData, team_size: e.target.value })}
        placeholder="10"
      />

      <div className="flex justify-end pt-4">
        <Button type="submit" loading={loading}>
          Continue
        </Button>
      </div>
    </form>
  );
}
