'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { FileUpload } from '@/components/ui/file-upload';
import { useOnboarding } from '@/lib/onboarding-context';
import { importDatabase } from '@/lib/api';

interface DatabaseImportStepProps {
  onNext: () => void;
  onBack: () => void;
  onSkip: () => void;
}

export function DatabaseImportStep({
  onNext,
  onBack,
  onSkip,
}: DatabaseImportStepProps) {
  const { state, setDatabaseImport } = useOnboarding();

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
      const result = await importDatabase(state.companyId, file);
      setDatabaseImport(result);
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
          Import your existing database
        </h2>
        <p className="mt-1 text-sm text-gray-500">
          Have past candidates or contacts? Import them here.
        </p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          {error}
        </div>
      )}

      {/* Instructions */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <h3 className="font-medium text-gray-900 mb-2">
          Expected CSV format:
        </h3>
        <p className="text-sm text-gray-600 mb-3">
          Your CSV should include columns like:
        </p>
        <div className="bg-white rounded border border-gray-200 p-3 font-mono text-xs overflow-x-auto">
          name,email,linkedin_url,company,title,skills,notes
        </div>
        <p className="text-xs text-gray-500 mt-2">
          Column names are flexible - we&apos;ll try to match common variations
        </p>
      </div>

      {/* File upload */}
      <FileUpload
        label="Upload your database (CSV)"
        accept=".csv"
        onFileSelect={setFile}
        helperText="Export from your ATS, spreadsheet, or CRM"
      />

      {/* What we accept */}
      <div className="border border-gray-200 rounded-lg p-4">
        <h3 className="font-medium text-gray-900 mb-2">
          We can import from:
        </h3>
        <div className="grid grid-cols-2 gap-2 text-sm text-gray-600">
          <div className="flex items-center gap-2">
            <svg
              className="w-4 h-4 text-gray-400"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                clipRule="evenodd"
              />
            </svg>
            Google Sheets export
          </div>
          <div className="flex items-center gap-2">
            <svg
              className="w-4 h-4 text-gray-400"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                clipRule="evenodd"
              />
            </svg>
            Excel spreadsheets
          </div>
          <div className="flex items-center gap-2">
            <svg
              className="w-4 h-4 text-gray-400"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                clipRule="evenodd"
              />
            </svg>
            ATS exports (Lever, Greenhouse)
          </div>
          <div className="flex items-center gap-2">
            <svg
              className="w-4 h-4 text-gray-400"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                clipRule="evenodd"
              />
            </svg>
            CRM exports
          </div>
        </div>
      </div>

      {/* Import result */}
      {state.databaseImport && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <h3 className="font-medium text-green-900 mb-2">Import successful!</h3>
          <div className="text-sm text-green-800 space-y-1">
            <p>Total records: {state.databaseImport.total_records}</p>
            <p>New contacts added: {state.databaseImport.records_created}</p>
            <p>
              Existing matched (merged): {state.databaseImport.records_matched}
            </p>
            {state.databaseImport.records_failed > 0 && (
              <p className="text-yellow-700">
                Failed: {state.databaseImport.records_failed}
              </p>
            )}
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
            Import Database
          </Button>
        </div>
      </div>
    </div>
  );
}
