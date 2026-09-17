import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { initializeAuth } from "@/auth/store";
import "./index.css";
import App from "./App.tsx";

void initializeAuth();

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
