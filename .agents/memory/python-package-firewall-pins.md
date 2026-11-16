---
name: Python package firewall pins
description: Handling a pinned Python dependency denied by Replit's package firewall in this project.
---

When Replit's package firewall rejects the exact PyJWT pin, check the latest compatible release and update the project dependency pin before retrying installation.

**Why:** The blocked pin prevented installation of the project's full requirements, while PyJWT 2.15.1 installed and imported successfully.

**How to apply:** If the firewall rejects this project's pinned PyJWT version again, verify compatibility and update only that dependency pin rather than leaving the requirements file un-installable.
