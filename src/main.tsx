import { StrictMode } from "react"
import { createRoot } from "react-dom/client"
// @ts-expect-error fontsource packages lack type declarations
import "@fontsource-variable/plus-jakarta-sans"
// @ts-expect-error fontsource packages lack type declarations
import "@fontsource/dm-serif-display"
import "./index.css"
import App from "./App"

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>
)
