import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'

for (const storage of [localStorage, sessionStorage]) {
  for (const key of Object.keys(storage)) {
    if (key.startsWith('metis-') && storage.getItem(key.replace(/^metis-/, 'fieldtofit-')) === null) {
      storage.setItem(key.replace(/^metis-/, 'fieldtofit-'), storage.getItem(key)!);
    }
  }
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
