import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "@copilotkit/react-core/v2/styles.css";
// The same stylesheets as the HTML pages, so the React Dashboard looks the same.
import "../../brsr_p6/rendering/templates/style.css";
import "../../brsr_p6/rendering/templates/dashboard.css";
import "./page.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
