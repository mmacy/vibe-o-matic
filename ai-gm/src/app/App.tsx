import TopBar from './components/TopBar'
import SettingsDrawer from './components/SettingsDrawer'
import JournalDrawer from './components/JournalDrawer'
import Home from '../pages/Home'

export default function App() {
  return (
    <div className="flex h-full flex-col">
      <TopBar />
      <main className="flex-1 overflow-hidden">
        <Home />
      </main>
      <SettingsDrawer />
      <JournalDrawer />
    </div>
  )
}
