import { useState, useCallback } from 'react';
import { createProfile } from '../../api/profiles';
import { useAppContext } from '../../context/AppContext';

interface CreateProfileFormProps {
  onClose: () => void;
}

export default function CreateProfileForm({ onClose }: CreateProfileFormProps) {
  const { refreshProfiles, setActiveProfile } = useAppContext();
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [sourceType, setSourceType] = useState('web');
  const [domain, setDomain] = useState('');
  const [crawlDepth, setCrawlDepth] = useState(2);
  const [localPath, setLocalPath] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);

    try {
      const req = {
        name: name.trim(),
        sourceType,
        description: description.trim() || undefined,
        webDomains: sourceType !== 'local' && domain ? [domain.trim()] : undefined,
        crawlDepth: sourceType !== 'local' ? crawlDepth : undefined,
        localPaths: sourceType !== 'web' && localPath ? [localPath.trim()] : undefined,
      };

      await createProfile(req);
      await refreshProfiles();
      await setActiveProfile(name.trim());
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create profile');
    } finally {
      setSubmitting(false);
    }
  }, [name, description, sourceType, domain, crawlDepth, localPath, refreshProfiles, setActiveProfile, onClose]);

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-panel border border-panel-border rounded-xl p-6 w-full max-w-lg shadow-2xl" onClick={e => e.stopPropagation()}>
        <h2 className="text-lg font-bold text-slate-100 mb-4">Create New Profile</h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Name */}
          <div>
            <label className="block text-xs text-slate-400 uppercase tracking-wider mb-1">Name</label>
            <input
              type="text"
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="my-docs"
              required
              className="w-full bg-base border border-panel-border rounded-md px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-accent"
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-xs text-slate-400 uppercase tracking-wider mb-1">Description</label>
            <input
              type="text"
              value={description}
              onChange={e => setDescription(e.target.value)}
              placeholder="My documentation knowledge base"
              className="w-full bg-base border border-panel-border rounded-md px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-accent"
            />
          </div>

          {/* Source Type */}
          <div>
            <label className="block text-xs text-slate-400 uppercase tracking-wider mb-1">Source Type</label>
            <select
              value={sourceType}
              onChange={e => setSourceType(e.target.value)}
              className="w-full bg-base border border-panel-border rounded-md px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-accent"
            >
              <option value="web">Web (crawl a website)</option>
              <option value="local">Local (files on disk)</option>
              <option value="mixed">Mixed (web + local)</option>
            </select>
          </div>

          {/* Web domain */}
          {sourceType !== 'local' && (
            <div>
              <label className="block text-xs text-slate-400 uppercase tracking-wider mb-1">Domain to crawl</label>
              <input
                type="text"
                value={domain}
                onChange={e => setDomain(e.target.value)}
                placeholder="https://docs.example.com"
                required={sourceType !== 'local'}
                className="w-full bg-base border border-panel-border rounded-md px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-accent"
              />
            </div>
          )}

          {/* Crawl depth */}
          {sourceType !== 'local' && (
            <div>
              <label className="block text-xs text-slate-400 uppercase tracking-wider mb-1">Crawl Depth</label>
              <input
                type="number"
                value={crawlDepth}
                onChange={e => setCrawlDepth(parseInt(e.target.value) || 2)}
                min={1}
                max={5}
                className="w-20 bg-base border border-panel-border rounded-md px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-accent"
              />
            </div>
          )}

          {/* Local path */}
          {sourceType !== 'web' && (
            <div>
              <label className="block text-xs text-slate-400 uppercase tracking-wider mb-1">Local Directory Path</label>
              <input
                type="text"
                value={localPath}
                onChange={e => setLocalPath(e.target.value)}
                placeholder="C:\docs\my-project"
                required={sourceType !== 'web'}
                className="w-full bg-base border border-panel-border rounded-md px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-accent"
              />
            </div>
          )}

          {error && <p className="text-sm text-red-400">{error}</p>}

          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm text-slate-400 hover:text-slate-200 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting || !name.trim()}
              className="bg-accent text-slate-900 font-semibold px-5 py-2 rounded-md text-sm hover:brightness-110 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
            >
              {submitting ? 'Creating...' : 'Create Profile'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
