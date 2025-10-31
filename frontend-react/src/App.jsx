import { SelectedKeywordsProvider } from "./SelectedKeywordsContext";
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import GroupsPage from './GroupsPage';
import GroupPage from './GroupPage';

function App() {
  return (
    <SelectedKeywordsProvider>
      <BrowserRouter>
        <nav className="w-full p-4 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-400 shadow flex gap-6 items-center justify-center sticky top-0 z-20">
          <Link to="/groups" className="text-white text-lg font-semibold hover:underline">Groups</Link>
        </nav>
        <Routes>
          <Route path="/groups" element={<GroupsPage />} />
          <Route path="/groups/:group_id" element={<GroupPage />} />
        </Routes>
      </BrowserRouter>
    </SelectedKeywordsProvider>
  );
}

export default App;
