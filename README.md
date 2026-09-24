# Touchline — our FPL mini-league

A small, mobile-friendly website for **Rank follows, my brother!**, FPL league **795551**. Friends can open the public website without signing in.

Home, Gameweeks, Monthly, Season and Predictions include real standings, manager profiles, awards, small charts and transparent statistical projections. No AI is used.

## Cost: ₹0

This uses a **public GitHub repository**, **GitHub Pages**, standard **ubuntu-latest GitHub Actions** runners and FPL's public, unauthenticated website endpoints. There is no database, paid API, AI API, external font, chart package, custom domain, subscription or billing-account requirement. Python uses only its standard library; the frontend has no dependencies.

Keep this repository public. Do not switch to a larger/paid Actions runner or buy a domain. The workflow refuses to run in a private repository. The small Pages deployment artifact is retained for one day; no Actions caches or extra artifacts are created.

GitHub's documentation: [free public Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages), [free standard public Actions runners](https://docs.github.com/en/billing/concepts/product-billing/github-actions). These are free services, not trials, under the current provider terms.

## Automatic updates

GitHub runs **Update FPL and publish site** every six hours, at 00:17, 06:17, 12:17 and 18:17 UTC (05:47, 11:47, 17:47 and 23:47 India time). Scheduled jobs may start later during busy periods.

The Python script fetches public FPL data and writes one consistent snapshot to `data/league.json`. All five pages read that same file. It commits the result and publishes the static site. Your computer does not need to be switched on, and visitors never call FPL directly.

Old captain details are cached in `.fpl-cache.json` to reduce requests. Latest completed GW details refresh each run; older details refresh weekly. Requests are spaced out and failures retry up to three times. If standings or a manager's history fail, the previous complete dataset is kept. Optional captain-detail failures retain previous values or show missing data. A delay notice appears after 18 hours without a successful refresh.

## Manually refresh the scores

1. Open this repository on GitHub and select **Actions** near the top.
2. Select **Update FPL and publish site** in the left sidebar.
3. Click **Run workflow**, keep the branch as **main**, then click the green **Run workflow** button.
4. Wait for the run to finish (usually a few minutes), then reload the website.

Only the owner needs a GitHub account to trigger updates. Friends just use the public website link. Reloading the website reads the latest saved data; it does not start an FPL API refresh.

If a scheduled workflow is ever disabled by GitHub after prolonged repository inactivity, go to the same Actions screen and choose **Enable workflow**. Successful data-refresh commits ordinarily keep this repository active.

## Where GitHub Pages is configured

Open the repository's **Settings → Pages**. Under **Build and deployment**, the source should be **GitHub Actions**. The public address is shown there. It uses GitHub's free `github.io` domain and HTTPS.

## Change league ID next season

1. Open `config.json` in this repository.
2. Click the pencil button to edit it.
3. Replace `795551` with your new classic mini-league ID. Keep the number unquoted.
4. Click **Commit changes** and save to **main**.
5. The workflow automatically retrieves the new league and publishes the website. Confirm the league name on the site.

Caches reset automatically when the season or league changes. Only the current FPL season is shown; old season archives are not a feature of this V1. If you change the update interval, change both the cron schedule in `.github/workflows/update-fpl.yml` and `refresh_hours` in `config.json`; that config field is the display label.

## Scoring explained

- **Current standings:** official FPL league rank, movement and total, which may be provisional during a live GW.
- **Completed GW:** both `finished` and `data_checked` must be true in FPL. Blank GWs are included once checked; unfinished GWs are excluded from averages and awards.
- **GW score:** FPL points minus transfer-hit cost. For example 67 points minus a 4-point hit = 63. The GW table shows both figures. Weekly awards use this net score; ties share awards.
- **Monthly score:** sum of net points for GWs whose deadline falls within the month, using UK time. These are our own monthly tables and may differ from official FPL phase tables' boundary-hit treatment.
- **Captain:** final captain/vice-captain multiplier applied to that player's FPL GW points, including triple captain. Final FPL picks already reflect substitutions. Missing optional captain data is never invented; partial season captain totals show coverage.
- **Bench:** FPL's `points_on_bench`, i.e. points left unused after final scoring. Bench Boost is already in the GW total; its bench value may be zero.
- **Historical positions:** reconstructed among today's league members, using net cumulative league points and fewer transfers as a tie-break, excluding Wildcard/Free Hit transfers. Past membership changes cannot be reconstructed. First GW/month movement is blank because there is no prior position. Biggest seasonal rise means the largest gain between two consecutive completed GWs.
- **Transfers/hits:** history's actual event transfer count and point cost. A free chip does not generate invented hits. Squad value is the latest public deadline value, without bank.
- **Projection:** 65% last-five average + 35% season average gives expected points per future GW. Add that times remaining GWs to the last completed total. This prevents counting an unfinished GW twice. Equal rounded totals share a rank. No fixture model, machine learning or simulation.
- **Power Rating:** 40% latest GW + 30% last-five average + 20% season average + 10% rank movement over the last five completed GWs. Each component is min–max scaled across league members; when all values tie everyone receives 50 for that component. Final rating is rounded to 0–100. This is relative form, not a probability.

The public FPL API is undocumented and can occasionally be unavailable or change. The site preserves the last successful snapshot and displays its timestamp. It is an independent fan project, not affiliated with the Premier League.

## Files and local preview (optional)

- `index.html`, `styles.css`, `app.js`: the website.
- `config.json`: league ID and update-interval display.
- `scripts/update_fpl.py`: fetch and process FPL data.
- `scripts/validate_snapshot.py`: check the saved snapshot.
- `data/league.json`: all site data in one atomic snapshot.
- `.github/workflows/update-fpl.yml`: automatic update and Pages deployment.
- `tests/test_stats.py`: checks for hits, ties, chips, missing data and projections.

With Python 3.9 or newer installed:

```sh
python3 scripts/update_fpl.py
python3 -m unittest discover -s tests -v
python3 scripts/validate_snapshot.py
python3 -m http.server 8765
```

Open `http://localhost:8765`. No installation command or API key is needed.
