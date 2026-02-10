import type { Profile } from '../../api/types';
import Badge from '../common/Badge';
import Card from '../common/Card';

interface ProfileInfoProps {
  profile: Profile;
}

const TYPE_COLORS: Record<string, string> = {
  web: 'blue',
  local: 'green',
  mixed: 'teal',
};

export default function ProfileInfo({ profile }: ProfileInfoProps) {
  return (
    <Card>
      <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-3">Profile Info</h3>
      <p className="text-lg font-medium text-slate-100 mb-1">{profile.description || profile.name}</p>
      <div className="flex items-center gap-2 text-sm text-slate-400">
        <Badge color={TYPE_COLORS[profile.source_type] || 'gray'}>{profile.source_type}</Badge>
        <span>{profile.path}</span>
      </div>
    </Card>
  );
}
