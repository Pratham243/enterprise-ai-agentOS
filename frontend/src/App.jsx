import { BrowserRouter, Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import AskAgent from "./pages/AskAgent";
import Documents from "./pages/Documents";
import Approvals from "./pages/Approvals";
import RiskScoring from "./pages/RiskScoring";
import Tools from "./pages/Tools";
import Evaluate from "./pages/Evaluate";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="ask" element={<AskAgent />} />
          <Route path="documents" element={<Documents />} />
          <Route path="approvals" element={<Approvals />} />
          <Route path="risk" element={<RiskScoring />} />
          <Route path="tools" element={<Tools />} />
          <Route path="evaluate" element={<Evaluate />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
