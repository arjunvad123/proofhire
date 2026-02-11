'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { TagInput } from '@/components/ui/tag-input';
import { useOnboarding } from '@/lib/onboarding-context';
import { createRole } from '@/lib/api';

interface RolesStepProps {
  onNext: () => void;
  onBack: () => void;
  onSkip: () => void;
}

const LEVELS = [
  { value: 'intern', label: 'Intern' },
  { value: 'junior', label: 'Junior' },
  { value: 'mid', label: 'Mid-level' },
  { value: 'senior', label: 'Senior' },
  { value: 'staff', label: 'Staff' },
  { value: 'principal', label: 'Principal' },
  { value: 'lead', label: 'Lead' },
  { value: 'manager', label: 'Manager' },
];

const DEPARTMENTS = [
  'Engineering',
  'Product',
  'Design',
  'Data',
  'Operations',
  'Marketing',
  'Sales',
  'Other',
];

export function RolesStep({ onNext, onBack, onSkip }: RolesStepProps) {
  const { state, addRole } = useOnboarding();

  const [formData, setFormData] = useState({
    title: '',
    level: '',
    department: '',
    required_skills: [] as string[],
    preferred_skills: [] as string[],
    years_experience_min: '',
    years_experience_max: '',
    description: '',
    location: '',
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(state.roles.length === 0);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!state.companyId) {
      setError('Company not found. Please go back and try again.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const role = await createRole(state.companyId, {
        title: formData.title,
        level: formData.level || undefined,
        department: formData.department || undefined,
        required_skills: formData.required_skills,
        preferred_skills: formData.preferred_skills,
        years_experience_min: formData.years_experience_min
          ? parseInt(formData.years_experience_min)
          : undefined,
        years_experience_max: formData.years_experience_max
          ? parseInt(formData.years_experience_max)
          : undefined,
        description: formData.description || undefined,
        location: formData.location || undefined,
      });

      addRole(role);

      // Reset form
      setFormData({
        title: '',
        level: '',
        department: '',
        required_skills: [],
        preferred_skills: [],
        years_experience_min: '',
        years_experience_max: '',
        description: '',
        location: '',
      });

      setShowForm(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add role');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-900">
          What roles are you hiring for?
        </h2>
        <p className="mt-1 text-sm text-gray-500">
          Add the positions you&apos;re looking to fill
        </p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          {error}
        </div>
      )}

      {/* Existing roles */}
      {state.roles.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-gray-700">Added Roles</h3>
          {state.roles.map((role) => (
            <div
              key={role.id}
              className="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
            >
              <div>
                <p className="font-medium text-gray-900">{role.title}</p>
                <p className="text-sm text-gray-500">
                  {[role.level, role.department, role.location]
                    .filter(Boolean)
                    .join(' · ')}
                </p>
              </div>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                Added
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Add role form */}
      {showForm ? (
        <form onSubmit={handleSubmit} className="space-y-4 border-t pt-6">
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Job Title *"
              value={formData.title}
              onChange={(e) =>
                setFormData({ ...formData, title: e.target.value })
              }
              placeholder="Senior Backend Engineer"
              required
            />
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Level
              </label>
              <select
                value={formData.level}
                onChange={(e) =>
                  setFormData({ ...formData, level: e.target.value })
                }
                className="block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">Select level</option>
                {LEVELS.map((level) => (
                  <option key={level.value} value={level.value}>
                    {level.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Department
              </label>
              <select
                value={formData.department}
                onChange={(e) =>
                  setFormData({ ...formData, department: e.target.value })
                }
                className="block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">Select department</option>
                {DEPARTMENTS.map((dept) => (
                  <option key={dept} value={dept}>
                    {dept}
                  </option>
                ))}
              </select>
            </div>
            <Input
              label="Location"
              value={formData.location}
              onChange={(e) =>
                setFormData({ ...formData, location: e.target.value })
              }
              placeholder="Remote, San Francisco, etc."
            />
          </div>

          <TagInput
            label="Required Skills"
            value={formData.required_skills}
            onChange={(tags) =>
              setFormData({ ...formData, required_skills: tags })
            }
            placeholder="Python, PostgreSQL, Docker..."
          />

          <TagInput
            label="Nice-to-Have Skills"
            value={formData.preferred_skills}
            onChange={(tags) =>
              setFormData({ ...formData, preferred_skills: tags })
            }
            placeholder="Kubernetes, ML experience..."
          />

          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Min Years Experience"
              type="number"
              value={formData.years_experience_min}
              onChange={(e) =>
                setFormData({ ...formData, years_experience_min: e.target.value })
              }
              placeholder="3"
            />
            <Input
              label="Max Years Experience"
              type="number"
              value={formData.years_experience_max}
              onChange={(e) =>
                setFormData({ ...formData, years_experience_max: e.target.value })
              }
              placeholder="8"
            />
          </div>

          <Textarea
            label="Job Description"
            value={formData.description}
            onChange={(e) =>
              setFormData({ ...formData, description: e.target.value })
            }
            rows={3}
            placeholder="Describe the role and responsibilities..."
          />

          <div className="flex justify-end gap-3 pt-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => setShowForm(false)}
            >
              Cancel
            </Button>
            <Button type="submit" loading={loading}>
              Add Role
            </Button>
          </div>
        </form>
      ) : (
        <Button
          type="button"
          variant="outline"
          onClick={() => setShowForm(true)}
          className="w-full"
        >
          + Add {state.roles.length > 0 ? 'Another' : 'a'} Role
        </Button>
      )}

      <div className="flex justify-between pt-4 border-t">
        <Button type="button" variant="outline" onClick={onBack}>
          Back
        </Button>
        <div className="flex gap-3">
          {state.roles.length === 0 && (
            <Button type="button" variant="ghost" onClick={onSkip}>
              Skip for now
            </Button>
          )}
          <Button
            type="button"
            onClick={onNext}
            disabled={showForm}
          >
            Continue
          </Button>
        </div>
      </div>
    </div>
  );
}
