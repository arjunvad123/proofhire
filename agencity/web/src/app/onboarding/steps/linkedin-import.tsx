'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { FileUpload } from '@/components/ui/file-upload';
import { useOnboarding } from '@/lib/onboarding-context';
import { importLinkedIn } from '@/lib/api';

interface LinkedInImportStepProps {
  onNext: () => void;
  onBack: () => void;
  onSkip: () => void;
}

export function LinkedInImportStep({
  onNext,
  onBack,
  onSkip,
}: LinkedInImportStepProps) {
  const { state, setLinkedinImport } = useOnboarding();

  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleImport = async () => {
    if (!file || !state.companyId) {
      setError('Please select a file first');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result = await importLinkedIn(state.companyId, file);
      setLinkedinImport(result);
      onNext();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Import failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-900">
          Import your LinkedIn network
        </h2>
        <p className="mt-1 text-sm text-gray-500">
          Your connections are a goldmine of potential candidates
        </p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          {error}
        </div>
      )}

      {/* Instructions */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="font-medium text-blue-900 mb-2">
          How to export your LinkedIn connections:
        </h3>
        <ol className="text-sm text-blue-800 space-y-2">
          <li>
            1. Go to{' '}
            <a
              href="https://www.linkedin.com/mypreferences/d/download-my-data"
              target="_blank"
              rel="noopener noreferrer"
              className="underline font-medium"
            >
              LinkedIn Data Export
            </a>
          </li>
          <li>2. Select &quot;Connections&quot; and click &quot;Request archive&quot;</li>
          <li>3. Wait for the email (usually takes 10 minutes)</li>
          <li>4. Download and extract the ZIP file</li>
          <li>5. Upload the &quot;Connections.csv&quot; file below</li>
        </ol>
      </div>

      {/* File upload */}
      <FileUpload
        label="Upload Connections.csv"
        accept=".csv"
        onFileSelect={setFile}
        helperText="Your data stays private and is only used to find matches"
      />

      {/* What we'll do */}
      <div className="bg-gray-50 rounded-lg p-4">
        <h3 className="font-medium text-gray-900 mb-2">What happens next:</h3>
        <ul className="text-sm text-gray-600 space-y-1">
          <li className="flex items-center gap-2">
            <svg
              className="w-4 h-4 text-green-500"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                clipRule="evenodd"
              />
            </svg>
            We import your connections into your private database
          </li>
          <li className="flex items-center gap-2">
            <svg
              className="w-4 h-4 text-green-500"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                clipRule="evenodd"
              />
            </svg>
            Profiles get enriched with public information
          </li>
          <li className="flex items-center gap-2">
            <svg
              className="w-4 h-4 text-green-500"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                clipRule="evenodd"
              />
            </svg>
            When you search, we highlight warm connections first
          </li>
        </ul>
      </div>

      {/* Import result */}
      {state.linkedinImport && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <h3 className="font-medium text-green-900 mb-2">Import successful!</h3>
          <div className="text-sm text-green-800 space-y-1">
            <p>Total records: {state.linkedinImport.total_records}</p>
            <p>New contacts added: {state.linkedinImport.records_created}</p>
            <p>Existing matched: {state.linkedinImport.records_matched}</p>
          </div>
        </div>
      )}

      <div className="flex justify-between pt-4">
        <Button type="button" variant="outline" onClick={onBack}>
          Back
        </Button>
        <div className="flex gap-3">
          <Button type="button" variant="ghost" onClick={onSkip}>
            Skip for now
          </Button>
          <Button
            type="button"
            onClick={handleImport}
            loading={loading}
            disabled={!file}
          >
            Import Connections
          </Button>
        </div>
      </div>
    </div>
  );
}
