# Part-time contract finder

A Python standard-library job for UK remote, part-time/fractional DevOps and platform contracts advertised outside IR35. No LLM, browser automation, application submission or server required.

## Setup

1. Copy these files, including `.github`, to the root of a **personal private GitHub repository**. The workflow expects `finder.py` and `config.json` at the root.
2. Obtain a Brave Search API subscription/key: https://api-dashboard.search.brave.com/. Check the current pricing and your plan's permitted use.
3. In repository Settings → Secrets and variables → Actions, add `BRAVE_SEARCH_API_KEY` as a repository secret.
4. Commit to the default branch. Enable Actions if needed.
5. Open Actions → Find part-time contracts → Run workflow.
6. Read the run summary or download `contract-shortlist` (Markdown and JSON).

Runs at 07:23 and 18:23 UTC daily (08:23/19:23 UK summer time, 07:23/18:23 UK winter time). Scheduled Actions may be delayed. Six queries per run, up to 20 results per query; retry budget is four attempts per query. Provider costs and GitHub usage depend on your plan.

## What the results establish

Candidates have explicit part-time/fractional/limited-days/evening/weekend, remote and outside-IR35 wording in search-result evidence plus a relevant role. Conflicting full-time, inside-IR35, hybrid or on-site wording is rejected conservatively. Missing evidence goes to a separate unconfirmed section.

**These are search-index candidates, not verified live vacancies.** Search snippets can merge unrelated text from listing pages. The script does not fetch adverts, bypass restrictions or guarantee vacancy availability. Verify the original page, IR35 wording, weekly commitment, UK residency requirements and working hours before applying. Index age is stored separately; it is not treated as the posting date. Rates and durations are not guessed.

Brave's last-month freshness filter helps discovery but is not a guarantee of an advert's age. Search results may omit qualifying jobs. No minimum rate has been invented. Edit `config.json` to adjust queries and report limits.

## Discovery history

The workflow restores `seen.json` from the most recent successful run's `discovery-state` artifact. It marks repeated canonical URLs as seen before; it does not drop them so you can revisit them. Tracking parameters are removed, but cross-site reposts are not deduplicated reliably.

Artifacts retain history for 90 days (subject to repository policy); this is continuity across normal daily runs, not permanent storage. Missing/deleted history causes restoration to fail visibly. The first run starts fresh. For permanent history, replace this with a durable database/object store. Concurrent runs are serialised.

## Security and operations

Only contents/actions read permissions. External descriptions are treated as data. No email or external notification is sent. Reports can contain third-party descriptions: keep the repository private. API errors omit response bodies; secrets are never printed. Requests have a timeout and bounded retry for 429/5xx. A search failure fails the run rather than reporting zero jobs. Actions are pinned to commit SHAs; maintain these pins with Dependabot.

## Local testing

```bash
python3 -m unittest discover -s tests -v
python3 finder.py --fixture tests/sample-results.json
```

For a live local run, provide `BRAVE_SEARCH_API_KEY` securely in your environment and run `python3 finder.py`. Do not commit the key. No Python packages are required.

API reference: https://api-dashboard.search.brave.com/app/documentation/web-search/codes
GitHub schedule reference: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule
