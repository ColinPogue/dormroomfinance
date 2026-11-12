# Dorm Room Finance makeover — November 12, 2026

Explicit user authorization covers implementation and publication to dormroomfinance.com. "drf.com" was interpreted as shorthand for the established domain; no domain purchase or migration is included.

Source baseline: main c7b931d5e69dd54abca5a1808d06ba7dd4f609d4; base tree 312f44861e0cc93a48886b64c92f5c7098e3e7bd. Source assembled through the GitHub connector into an isolated local directory because terminal DNS cannot resolve github.com. The original dirty checkout was preserved. All 142 remote text files fetched; the theme revision matches 10d3dcc0e05cee0aaca58a1305a9d824b2cf9a2a. Existing remote static assets are preserved in the release tree; local preview copies have one different ETF thumbnail, which is not included as a release change.

Changes: responsive homepage and navigation; reader roadmap; redesigned cards/article reading layout and footer; local search; budget calculator and CSV export; internship worksheet; source notes and real update dates on 21 substantive article refreshes; archive notices on remaining 79; corrected stale Chase product recommendation, income-driven repayment framing, capitalization claims, and broken internal link; removed duplicate heading; unified author bio and truthful AI/editorial disclosures; scheduler changes to researched drafts only; pinned Hugo build and automated validation.

Validation: Hugo 0.157.0 production build; 100 original article routes and canonical URLs; generated internal links and resource paths; calculator math with positive/zero/negative/fractional/invalid values; research source gating, stale/future dates, and mismatched topics. GitHub run 43257830148 passed the production build, rendered-page validation, source checks, budget math, and browser behavior tests on ubuntu-24.04. Browser smoke script tests 1440/390/320px layouts, navigation, horizontal overflow, image loading, search, calculation updates, invalid input, and CSV download. GitHub branch validation must pass before production ref moves. Screenshots are retained as a GitHub Actions artifact.

Local browser launch and loopback server are blocked by the runtime sandbox; do not claim local browser rendering was inspected. GitHub browser test results must be recorded separately after execution. Screenshots provide review artifacts; automated layout assertions are not a human visual inspection.

The October traffic drop remains undiagnosed without Search Console indexing reports. No traffic result is guaranteed. The 79 archive articles remain a review backlog. A source age check is not a fact-check by itself. No new tracking, signup, paid service, domain, bank connection, or unrelated policy update is introduced.

Runtime rollout: after website validation, install only the three new draft-only automation modules plus research.py into the existing scheduled project, preserving exact originals in a local backup directory and preserving its publisher.py, progress.json, last_run.json, environment, images, and LaunchAgent schedule. The GitHub article pipeline is otherwise no longer called by main.py. No API generation or publication is needed to check the empty research queue.

Rollback: restore only the release's modified paths from the recorded pre-release commit using a new normal commit if needed; never reset/stash/rebase the user's working checkout. Preserve later commits. The local automation backup can restore pre-makeover modules if explicitly required, but restoring unreviewed automatic publication would undo the new editorial safeguard.

Final visual review: GitHub run 43258046361 passed all browser tests. Compact 1440px desktop and 390px mobile homepage screenshots were retrieved from the job logs and inspected locally; navigation, hero, spacing, and first-screen hierarchy render coherently. Full-page screenshots are retained in the run artifact. This is a representative homepage visual check, not an exhaustive physical-device audit.

Post-deploy verification is performed against the actual dormroomfinance.com URLs by scripts/verify_live.py from the deployment runner; results must be recorded after deployment.
