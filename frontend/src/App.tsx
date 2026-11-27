import { BrowserRouter, Routes, Route, NavLink, Navigate, Outlet, useNavigate } from "react-router-dom";
import { getToken, setToken } from "./api";
import { AuthPage, SearchPage, ComparePage, BookmarksPage } from "./pages";

function Shell() {
  const nav = useNavigate();
  if (!getToken()) return <Navigate to="/login" replace />;
  return (
    <div className="shell">
      <nav className="rail" aria-label="Main">
        <div className="brand">Prep<span>Lens</span></div>
        <NavLink to="/search">Search</NavLink>
        <NavLink to="/compare">Compare</NavLink>
        <NavLink to="/bookmarks">Bookmarks</NavLink>
        <button className="link" onClick={() => { setToken(null); nav("/login"); }}>Sign out</button>
      </nav>
      <main className="content"><Outlet /></main>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<AuthPage />} />
        <Route element={<Shell />}>
          <Route path="/search" element={<SearchPage />} />
          <Route path="/compare" element={<ComparePage />} />
          <Route path="/bookmarks" element={<BookmarksPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/search" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
