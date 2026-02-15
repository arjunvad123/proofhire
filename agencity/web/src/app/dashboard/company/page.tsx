'use client';

import { useEffect, useState } from 'react';
import { CompanyWithStats, getCompany, updateCompany, getRoles, Role } from '@/lib/api';
import { Button } from '@/components/ui/button';

export default function CompanyPage() {
    const [mounted, setMounted] = useState(false);
    const [company, setCompany] = useState<CompanyWithStats | null>(null);
    const [roles, setRoles] = useState<Role[]>([]);
    const [loading, setLoading] = useState(true);
    const [rolesLoading, setRolesLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [editing, setEditing] = useState(false);
    const [activeTab, setActiveTab] = useState<'profile' | 'roles'>('profile');
    const [expandedRoleId, setExpandedRoleId] = useState<string | null>(null);
    const [formData, setFormData] = useState<{
        name: string;
        domain: string;
        industry: string;
        tech_stack: string;
    }>({
        name: '',
        domain: '',
        industry: '',
        tech_stack: '',
    });

    useEffect(() => {
        setMounted(true);
        loadCompany();
    }, []);

    useEffect(() => {
        if (activeTab === 'roles' && company && !rolesLoading && roles.length === 0) {
            loadRoles();
        }
    }, [activeTab]);

    async function loadCompany() {
        try {
            setLoading(true);
            const saved = localStorage.getItem('onboarding-state');
            let companyId = '';
            if (saved) {
                const state = JSON.parse(saved);
                companyId = state.company?.id;
            }

            if (!companyId) {
                setLoading(false);
                return;
            }

            const data = await getCompany(companyId);
            setCompany(data);
            setFormData({
                name: data.name,
                domain: data.domain || '',
                industry: data.industry || '',
                tech_stack: data.tech_stack.join(', '),
            });
        } catch (err) {
            setError('Failed to load company details');
            console.error(err);
        } finally {
            setLoading(false);
        }
    }

    async function loadRoles() {
        if (!company) return;
        try {
            setRolesLoading(true);
            const rolesData = await getRoles(company.id);
            setRoles(rolesData);
        } catch (err) {
            setError('Failed to load roles');
            console.error(err);
        } finally {
            setRolesLoading(false);
        }
    }

    async function handleSave() {
        if (!company) return;

        try {
            setLoading(true);
            await updateCompany(company.id, {
                name: formData.name,
                domain: formData.domain,
                industry: formData.industry,
                tech_stack: formData.tech_stack.split(',').map(s => s.trim()).filter(Boolean),
            });
            setEditing(false);
            loadCompany(); // Reload to get fresh data
        } catch (err) {
            setError('Failed to update company');
            console.error(err);
        } finally {
            setLoading(false);
        }
    }

    const StatCard = ({ label, value }: { label: string; value: number | string }) => (
        <div className="bg-white p-6 rounded-xl border border-gray-200">
            <div className="text-sm text-gray-500 font-medium">{label}</div>
            <div className="mt-2 text-3xl font-bold text-gray-900">{value}</div>
        </div>
    );

    const formatDate = (dateString: string) => {
        const date = new Date(dateString);
        const now = new Date();
        const diffInMs = now.getTime() - date.getTime();
        const diffInDays = Math.floor(diffInMs / (1000 * 60 * 60 * 24));

        if (diffInDays === 0) return 'Today';
        if (diffInDays === 1) return 'Yesterday';
        if (diffInDays < 7) return `${diffInDays} days ago`;
        if (diffInDays < 30) return `${Math.floor(diffInDays / 7)} weeks ago`;
        return date.toLocaleDateString();
    };

    const getStatusBadgeColor = (status: string) => {
        switch (status.toLowerCase()) {
            case 'active':
                return 'bg-green-100 text-green-800';
            case 'inactive':
                return 'bg-gray-100 text-gray-800';
            case 'closed':
                return 'bg-red-100 text-red-800';
            default:
                return 'bg-gray-100 text-gray-800';
        }
    };

    // Prevent hydration mismatch
    if (!mounted) {
        return (
            <div className="space-y-6 animate-pulse">
                <div className="h-8 w-48 bg-gray-200 rounded"></div>
                <div className="grid grid-cols-3 gap-6">
                    <div className="h-32 bg-gray-200 rounded-xl"></div>
                    <div className="h-32 bg-gray-200 rounded-xl"></div>
                    <div className="h-32 bg-gray-200 rounded-xl"></div>
                </div>
            </div>
        );
    }

    if (!company && !loading) {
        return (
            <div className="text-center py-12">
                <p className="text-gray-600">Please complete onboarding first</p>
            </div>
        );
    }

    if (loading && !company) {
        return (
            <div className="space-y-6 animate-pulse">
                <div className="h-8 w-48 bg-gray-200 rounded"></div>
                <div className="grid grid-cols-3 gap-6">
                    <div className="h-32 bg-gray-200 rounded-xl"></div>
                    <div className="h-32 bg-gray-200 rounded-xl"></div>
                    <div className="h-32 bg-gray-200 rounded-xl"></div>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-8">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">{company?.name}</h1>
                    <p className="text-gray-500 mt-1">{company?.domain || 'No domain set'}</p>
                </div>
                {activeTab === 'profile' && (
                    <Button
                        variant={editing ? "outline" : undefined}
                        onClick={() => editing ? setEditing(false) : setEditing(true)}
                    >
                        {editing ? 'Cancel' : 'Edit Details'}
                    </Button>
                )}
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <StatCard label="Total Candidates" value={company?.people_count || 0} />
                <StatCard label="Active Roles" value={company?.roles_count || 0} />
                <StatCard label="Network Size" value={company?.people_count ? Math.round(company.people_count * 0.8) : 0} /> {/* Estimated */}
            </div>

            {/* Tabs Navigation */}
            <div className="border-b border-gray-200">
                <div className="flex gap-8">
                    <button
                        onClick={() => setActiveTab('profile')}
                        className={`px-1 py-4 font-medium border-b-2 transition-colors ${activeTab === 'profile'
                                ? 'text-blue-700 border-blue-700'
                                : 'text-gray-600 border-transparent hover:text-gray-900'
                            }`}
                    >
                        Company Profile
                    </button>
                    <button
                        onClick={() => setActiveTab('roles')}
                        className={`px-1 py-4 font-medium border-b-2 transition-colors ${activeTab === 'roles'
                                ? 'text-blue-700 border-blue-700'
                                : 'text-gray-600 border-transparent hover:text-gray-900'
                            }`}
                    >
                        Active Roles
                    </button>
                </div>
            </div>

            {/* Tab Content */}
            {activeTab === 'profile' ? (
                <>
                    {/* Details Form / View */}
                    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
                        <div className="p-6 border-b border-gray-200">
                            <h2 className="text-lg font-semibold text-gray-900">Company Profile</h2>
                        </div>

                        <div className="p-6 space-y-6">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Company Name
                                    </label>
                                    {editing ? (
                                        <input
                                            type="text"
                                            value={formData.name}
                                            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                                        />
                                    ) : (
                                        <div className="text-gray-900 py-2">{company?.name}</div>
                                    )}
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Domain
                                    </label>
                                    {editing ? (
                                        <input
                                            type="text"
                                            value={formData.domain}
                                            onChange={(e) => setFormData({ ...formData, domain: e.target.value })}
                                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                                        />
                                    ) : (
                                        <div className="text-gray-900 py-2">{company?.domain || '-'}</div>
                                    )}
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Industry
                                    </label>
                                    {editing ? (
                                        <input
                                            type="text"
                                            value={formData.industry}
                                            onChange={(e) => setFormData({ ...formData, industry: e.target.value })}
                                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                                        />
                                    ) : (
                                        <div className="text-gray-900 py-2">{company?.industry || '-'}</div>
                                    )}
                                </div>

                                <div className="col-span-2">
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Tech Stack
                                    </label>
                                    {editing ? (
                                        <textarea
                                            value={formData.tech_stack}
                                            onChange={(e) => setFormData({ ...formData, tech_stack: e.target.value })}
                                            placeholder="React, Node.js, Python..."
                                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                                            rows={3}
                                        />
                                    ) : (
                                        <div className="flex flex-wrap gap-2 py-2">
                                            {company?.tech_stack.map((tech, i) => (
                                                <span key={i} className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-sm">
                                                    {tech}
                                                </span>
                                            ))}
                                            {(!company?.tech_stack || company.tech_stack.length === 0) && (
                                                <span className="text-gray-400">No tech stack defined</span>
                                            )}
                                        </div>
                                    )}
                                </div>
                            </div>

                            {editing && (
                                <div className="flex justify-end pt-4">
                                    <Button onClick={handleSave} loading={loading}>
                                        Save Changes
                                    </Button>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Founder Info */}
                    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
                        <div className="p-6 border-b border-gray-200">
                            <h2 className="text-lg font-semibold text-gray-900">Founder Information</h2>
                        </div>
                        <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">Name</label>
                                <div className="text-gray-900">{company?.founder_name}</div>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
                                <div className="text-gray-900">{company?.founder_email}</div>
                            </div>
                            {company?.founder_linkedin_url && (
                                <div className="col-span-2">
                                    <label className="block text-sm font-medium text-gray-700 mb-2">LinkedIn</label>
                                    <a href={company.founder_linkedin_url} target="_blank" rel="noopener noreferrer text-blue-600 hover:underline">
                                        {company.founder_linkedin_url}
                                    </a>
                                </div>
                            )}
                        </div>
                    </div>
                </>
            ) : (
                /* Active Roles Tab Content */
                <div className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
                    {rolesLoading ? (
                        <div className="p-8 text-center text-gray-500 text-sm">Loading roles...</div>
                    ) : roles.length === 0 ? (
                        <div className="p-8 text-center text-gray-500 text-sm">No active roles found. Create your first role to get started.</div>
                    ) : (
                        <div className="divide-y divide-gray-200">
                            {roles.map((role) => (
                                <div key={role.id}>
                                    {/* Role Row */}
                                    <button
                                        onClick={() => setExpandedRoleId(expandedRoleId === role.id ? null : role.id)}
                                        className="w-full text-left hover:bg-gray-50 transition-colors p-0"
                                    >
                                        <table className="w-full">
                                            <tbody>
                                                <tr>
                                                    <td className="px-4 py-3 whitespace-nowrap">
                                                        <div className="flex items-center gap-3">
                                                            <div className="text-lg text-gray-400">
                                                                {expandedRoleId === role.id ? '▼' : '▶'}
                                                            </div>
                                                            <div className="text-sm font-medium text-gray-900">{role.title}</div>
                                                        </div>
                                                    </td>
                                                    <td className="px-4 py-3 whitespace-nowrap">
                                                        <div className="text-sm text-gray-900">{role.level || '-'}</div>
                                                    </td>
                                                    <td className="px-4 py-3 whitespace-nowrap">
                                                        <div className="text-sm text-gray-900">{role.department || '-'}</div>
                                                    </td>
                                                    <td className="px-4 py-3 whitespace-nowrap">
                                                        <div className="text-sm text-gray-900">{role.location || '-'}</div>
                                                    </td>
                                                    <td className="px-4 py-3 whitespace-nowrap">
                                                        <div className="text-sm text-gray-900">
                                                            {role.years_experience_min || role.years_experience_max
                                                                ? `${role.years_experience_min || 0}-${role.years_experience_max || '0+'} yrs`
                                                                : '-'}
                                                        </div>
                                                    </td>
                                                    <td className="px-4 py-3 whitespace-nowrap">
                                                        <span className={`px-2 py-0.5 inline-flex text-xs leading-4 font-semibold rounded-full ${getStatusBadgeColor(role.status)}`}>
                                                            {role.status || 'Unknown'}
                                                        </span>
                                                    </td>
                                                    <td className="px-4 py-3 whitespace-nowrap">
                                                        <div className="text-sm text-gray-500">{formatDate(role.created_at)}</div>
                                                    </td>
                                                </tr>
                                            </tbody>
                                        </table>
                                    </button>

                                    {/* Expanded Details */}
                                    {expandedRoleId === role.id && (
                                        <div className="bg-gray-50 border-t border-gray-200 px-4 py-6">
                                            <div className="max-w-4xl space-y-6">
                                                {/* Job Description */}
                                                {role.description && (
                                                    <div>
                                                        <h3 className="text-sm font-semibold text-gray-900 mb-2">Job Description</h3>
                                                        <p className="text-sm text-gray-700 leading-relaxed">{role.description}</p>
                                                    </div>
                                                )}

                                                {/* Required Skills */}
                                                {role.required_skills && role.required_skills.length > 0 && (
                                                    <div>
                                                        <h3 className="text-sm font-semibold text-gray-900 mb-2">Required Skills</h3>
                                                        <div className="flex flex-wrap gap-2">
                                                            {role.required_skills.map((skill, i) => (
                                                                <span key={i} className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                                                    {skill}
                                                                </span>
                                                            ))}
                                                        </div>
                                                    </div>
                                                )}

                                                {/* Preferred Skills */}
                                                {role.preferred_skills && role.preferred_skills.length > 0 && (
                                                    <div>
                                                        <h3 className="text-sm font-semibold text-gray-900 mb-2">Preferred Skills</h3>
                                                        <div className="flex flex-wrap gap-2">
                                                            {role.preferred_skills.map((skill, i) => (
                                                                <span key={i} className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                                                                    {skill}
                                                                </span>
                                                            ))}
                                                        </div>
                                                    </div>
                                                )}

                                                {/* Salary Range */}
                                                {(role.salary_min || role.salary_max) && (
                                                    <div>
                                                        <h3 className="text-sm font-semibold text-gray-900 mb-2">Compensation</h3>
                                                        <p className="text-sm text-gray-700">
                                                            {role.salary_min && role.salary_max
                                                                ? `$${(role.salary_min / 1000).toFixed(0)}k - $${(role.salary_max / 1000).toFixed(0)}k`
                                                                : role.salary_min
                                                                    ? `From $${(role.salary_min / 1000).toFixed(0)}k`
                                                                    : `Up to $${((role.salary_max || 0) / 1000).toFixed(0)}k`}
                                                        </p>
                                                    </div>
                                                )}

                                                {/* Additional Details Grid */}
                                                <div className="grid grid-cols-2 gap-4 pt-2">
                                                    {role.level && (
                                                        <div className="bg-white p-3 rounded border border-gray-200">
                                                            <p className="text-xs text-gray-500 font-medium">Level</p>
                                                            <p className="text-sm text-gray-900">{role.level}</p>
                                                        </div>
                                                    )}
                                                    {role.department && (
                                                        <div className="bg-white p-3 rounded border border-gray-200">
                                                            <p className="text-xs text-gray-500 font-medium">Department</p>
                                                            <p className="text-sm text-gray-900">{role.department}</p>
                                                        </div>
                                                    )}
                                                    {role.location && (
                                                        <div className="bg-white p-3 rounded border border-gray-200">
                                                            <p className="text-xs text-gray-500 font-medium">Location</p>
                                                            <p className="text-sm text-gray-900">{role.location}</p>
                                                        </div>
                                                    )}
                                                    {(role.years_experience_min || role.years_experience_max) && (
                                                        <div className="bg-white p-3 rounded border border-gray-200">
                                                            <p className="text-xs text-gray-500 font-medium">Experience Required</p>
                                                            <p className="text-sm text-gray-900">
                                                                {role.years_experience_min || 0}-{role.years_experience_max || '0+'} years
                                                            </p>
                                                        </div>
                                                    )}
                                                </div>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
