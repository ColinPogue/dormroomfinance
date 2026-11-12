# Research and release workflow

The scheduled writer saves drafts only. There is no automatic public release. The existing scheduler timing is retained; the obsolete "daily" and "MWF" website claims were removed. Current user LaunchAgent configuration is Tuesday, Thursday, Saturday at 9 AM, not the tracked historical plist.

For a topic in automation/keywords.json, create research/<keyword-slug>.json with keyword, reviewed_by, and sources. Each source must have url (HTTPS, no credentials), verified_on (YYYY-MM-DD, within 14 days), and claims (a nonempty array of individually checked facts). Example:

```json
{
  "keyword": "your exact queued keyword",
  "reviewed_by": "Editor name",
  "sources": [{
    "url": "https://www.consumerfinance.gov/consumer-tools/credit-cards/",
    "verified_on": "YYYY-MM-DD",
    "claims": ["A specific fact you checked on this page"]
  }]
}
```

The date check does not itself verify a claim: the named editor must actually open the source and check its meaning. Drafts are saved outside Hugo's content directory in editorial-drafts, with draft:true. Expired source notes and already-published or drafted topics are skipped. Exhausting the queue does not reset completed keywords.

Before release: verify every important factual claim against the linked source; remove unsupported first-person experience; check product availability, eligibility, costs, and limitations; validate financial examples; review the rendered mobile and desktop page. Set the publication date to the actual original release date, add reviewed/lastmod only after substantive changes, and set draft:false only in the reviewed public copy. Build with the pinned Hugo version and run the validation scripts. Publish the complete release through the authorized GitHub workflow. Update local progress only after publication and deployment succeed.

Archive articles are labeled visibly. docs/content-audit.json lists all 100 original URLs, automated risk flags, and whether a substantive sourced refresh was completed. A risk flag is a review aid, not proof of an error. Do not call the remaining archive fully fact-checked.
