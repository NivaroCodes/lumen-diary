import { BrowserRouter, Navigate, Route, Routes } from 'react-router'
import Layout from './components/layout/Layout'
import ArchivePage from './pages/ArchivePage'
import CreateDayPage from './pages/CreateDayPage'
import MemoryPage from './pages/MemoryPage'
import NotFoundPage from './pages/NotFoundPage'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<CreateDayPage />} />
          <Route path="memory/:id" element={<MemoryPage />} />
          <Route path="memory" element={<Navigate to="/archive" replace />} />
          <Route path="archive" element={<ArchivePage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
