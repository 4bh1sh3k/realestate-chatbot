# Frontend Revert Guide

You have 3 complete frontend versions saved in your `frontend/` directory so you can switch between them in seconds:

| File | Style | Description |
|---|---|---|
| `frontend/index_minimal.html` | **Super Minimal** | Bare-bones 2-card testbed (no animations, just query + answer + chunks). |
| `frontend/index_dribbble.html` | **Q'Chat Dark UI** | The dark-mode landing page with glow gradients. |
| `frontend/index_backup.html` | **Original Real Estate** | The very first landing page with property cards & popup widget. |
| `frontend/index.html` | **Framer Bento UI** | The Framer Motion aesthetic with animated cards & grid. |

---

## How to Revert

To instantly go back to the super minimal version, run this in PowerShell:
```powershell
Copy-Item frontend/index_minimal.html frontend/index.html
```

To go back to the Q'Chat Dribbble version:
```powershell
Copy-Item frontend/index_dribbble.html frontend/index.html
```

To go back to the original real estate site:
```powershell
Copy-Item frontend/index_backup.html frontend/index.html
```
Then refresh `http://localhost:3000`!
