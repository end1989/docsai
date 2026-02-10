import { useState } from 'react';
import { AppProvider } from './context/AppContext';
import { useHealth } from './hooks/useHealth';
import Header from './components/layout/Header';
import TabNav, { type Tab } from './components/layout/TabNav';
import StatusBar from './components/layout/StatusBar';
import ChatPanel from './components/chat/ChatPanel';
import DashboardPanel from './components/dashboard/DashboardPanel';
import CreateProfileForm from './components/profile/CreateProfileForm';

function AppContent() {
  const [tab, setTab] = useState<Tab>('chat');
  const [showCreate, setShowCreate] = useState(false);
  useHealth();

  return (
    <div className="h-full flex flex-col bg-base">
      <Header onCreateProfile={() => setShowCreate(true)} />
      <TabNav active={tab} onChange={setTab} />
      <main className="flex-1 overflow-auto p-4">
        {tab === 'chat' && <ChatPanel />}
        {tab === 'dashboard' && <DashboardPanel />}
      </main>
      <StatusBar />
      {showCreate && <CreateProfileForm onClose={() => setShowCreate(false)} />}
    </div>
  );
}

export default function App() {
  return (
    <AppProvider>
      <AppContent />
    </AppProvider>
  );
}
