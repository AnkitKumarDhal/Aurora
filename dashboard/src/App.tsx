import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import LoginPage from "./pages/LoginPage";
import QueuePage from "./pages/QueuePage";
import PatientDetailPage from "./pages/PatientDetailPage";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/queue" element={<QueuePage />} />
        <Route path="/patient/:id" element={<PatientDetailPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
