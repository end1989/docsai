import type { ReactNode } from 'react';

export default function Card({ children, className = '' }: { children: ReactNode; className?: string }) {
  return (
    <div className={`bg-panel border border-panel-border rounded-lg p-4 ${className}`}>
      {children}
    </div>
  );
}
