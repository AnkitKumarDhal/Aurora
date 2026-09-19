import { DoctorsPanel } from "@/components/DoctorsPanel";
import { Header } from "@/components/Header";
import { PatientBoard } from "@/components/PatientBoard";
import { PatientDrawer } from "@/components/PatientDrawer";
import { PromotionPanel } from "@/components/PromotionPanel";
import { StatsStrip } from "@/components/StatsStrip";
import { Toast } from "@/components/Toast";

export default function App() {
  return (
    <div className="app">
      <Header />
      <StatsStrip />

      <div className="main">
        <PatientBoard />

        <aside className="sidebar">
          <DoctorsPanel />
          <PromotionPanel />
        </aside>
      </div>

      <PatientDrawer />
      <Toast />
    </div>
  );
}
