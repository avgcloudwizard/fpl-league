# Wireless — our FPL mini-league

**Website:** [avgcloudwizard.github.io/fpl-league](https://avgcloudwizard.github.io/fpl-league/)

**Manual refresh:** [Open the update workflow](https://github.com/avgcloudwizard/fpl-league/actions/workflows/update-fpl.yml)

A small, mobile-friendly website for **Rank follows, my brother!**, FPL league **795551**. Friends can open the public website without signing in.

Home, Season, Gameweeks, Monthly, Predictions, Prices and Content Creators include real standings, manager profiles, awards, small charts and transparent statistical projections. No AI is used.

## Cost: ₹0

This uses a **public GitHub repository**, **GitHub Pages**, standard **ubuntu-latest GitHub Actions** runners and FPL's public, unauthenticated website endpoints. There is no database, paid API, AI API, external font, chart package, custom domain, subscription or billing-account requirement. Python uses only its standard library; the frontend has no dependencies.

Keep this repository public. Do not switch to a larger/paid Actions runner or buy a domain. The workflow refuses to run in a private repository. The small Pages deployment artifact is retained for one day; no Actions caches or extra artifacts are created.

GitHub's documentation: [free public Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages), [free standard public Actions runners](https://docs.github.com/en/billing/concepts/product-billing/github-actions). These are free services, not trials, under the current provider terms.

## Automatic updates

GitHub checks the schedule every 15 minutes. Full data refreshes run from 45 minutes before a scheduled match until five hours after kickoff; outside those windows, approximately every six hours. Standard public-repository runners keep this at ₹0. Scheduled jobs can start late. An open website checks its own saved JSON once per minute without calling FPL; profiles and active searches are not interrupted.

The Python script fetches public FPL data and writes one consistent snapshot to `data/league.json`. All pages read that same file. It commits the result and publishes the static site. Your computer does not need to be switched on, and visitors never call FPL directly.

Old player picks and scoring contributions are cached in `.fpl-cache.json` to reduce requests. Latest completed GW details refresh each run; older details refresh weekly. Requests are spaced out and failures retry up to three times. If standings or a manager's history fail, the previous complete dataset is kept. Optional player-detail failures retain previous values or show missing data; MVP is shown only when every completed GW is covered. A delay notice appears after 18 hours without a successful refresh.

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

Caches reset automatically when the season or league changes. Only the current FPL season is shown; old season archives are not a feature of this V1. The schedule is configured in `.github/workflows/update-fpl.yml` and `scripts/refresh_due.py`; `config.json` stores the interval labels and prize amounts.

## Scoring explained

- **Current standings:** official FPL league rank, movement and total, which may be provisional during a live GW.
- **Completed GW:** both `finished` and `data_checked` must be true in FPL. Blank GWs are included once checked; unfinished GWs are excluded from averages and awards.
- **GW score:** FPL points minus transfer-hit cost. For example 67 points minus a 4-point hit = 63. The GW table shows both figures. Weekly awards use this net score; ties share awards.
- **Monthly score:** sum of net points for GWs whose deadline falls within the month, using UK time. These are our own monthly tables and may differ from official FPL phase tables' boundary-hit treatment.
- **Captain:** final captain/vice-captain multiplier applied to that player's FPL GW points, including triple captain. Final FPL picks already reflect substitutions. Missing optional captain data is never invented; partial season captain totals show coverage.
- **Bench:** FPL's `points_on_bench`, i.e. points left unused after final scoring. Bench Boost is already in the GW total; its bench value may be zero.
- **Historical positions:** reconstructed among today's league members, using net cumulative league points and fewer transfers as a tie-break, excluding Wildcard/Free Hit transfers. Past membership changes cannot be reconstructed. First GW/month movement is blank because there is no prior position.
- **Transfers made so far/hits:** FPL history's event transfer count and point cost. The transfer count excludes Wildcard/Free Hit moves, matching FPL's public total. Squad value is the latest public deadline value, without bank.
- **FTs:** the free-transfer allowance entering the next GW, reconstructed from public deadline history and capped at five. After the first GW it starts at one. Each normal GW spends the transfers made and adds the next GW's one free transfer, up to five. Wildcard/Free Hit retain the existing allowance rather than adding an extra transfer. Late starters are handled from their first deadline. The asterisk matters: transfers made since the latest deadline remain private, so this is not a claim about their exact remaining private balance. [Official FT/chip FAQ](https://www.premierleague.com/en/news/4661030).
- **Live rank:** the public `summary_overall_rank` from each manager's entry, showing their overall FPL rank as of our latest snapshot, roughly every 15 minutes around matches and six hours otherwise. Official ranks update during matches, but this saved snapshot is not instantaneous. The league-position column remains separate.
- **Chips:** the public chip history appears as small BB/TC/WC/FH badges with GW numbers. Colours are blue/yellow/red/green respectively.
- **Best/worst:** the net score includes its GW number in brackets. Equal best/worst scores list every matching GW. Lowest historical position and displayed average-score metrics are removed; highest position is the final season-table column. Averages remain internal inputs to the Power Rating and projection formulas.
- **MVP:** sum of each player's points actually earned for the manager across completed GWs. Final picks multipliers include captain/triple captain, autosubs and Bench Boost; unused bench points do not count. Transfer hits are a team cost and are not assigned to a player. Tied MVPs are all shown. A player who was later sold can still be MVP. If any GW's player contributions are missing or do not reconcile to the official gross GW score, no MVP is asserted. Miniature portraits use the same free public Premier League image host as the FPL site, with an initials fallback.
- **Projection:** deterministic form and chip arithmetic, with no random adjustment. Form = 65% last-five net average + 35% season net average. Expected ordinary GW points = 50 + (completed count / (completed count + 10)) × (form − 50). Unused chips add estimated bonuses: Wildcard 8, Free Hit 8, Triple Captain 8, Bench Boost 12, within official chip windows and available one-chip-per-GW slots. Expired first-half chips cannot carry over. A conservative 2,430-point envelope smoothly dampens the projected future contribution: for remaining room R and raw future points F, contribution = F / (1 + (F/R)^8)^(1/8). This is an assumption, not a historical maximum or confidence interval. Actual earned scores are never reduced, even above the envelope. No future projection remains after the final GW. Equal rounded projections share a finishing rank. Fixtures and injuries are not modelled.
- **Best GW rank:** the smallest official overall Gameweek rank (`history.current[].rank`) achieved by any manager, with the GW number. This is separate from overall season rank and mini-league GW rank.
- **Captaincy failures:** completed GWs where the effective captain scored at most 4 base points, before the captain or Triple Captain multiplier. Final vice-captain fallback is respected; if neither captain plays, the original captain’s zero is a failure. Winner cards also list the failed captain names and counts.
- **Hauls caught:** one count per scoring player per completed GW with at least 12 base points. A captain still counts once; an unused bench player does not count. Autosubs and Bench Boost follow final FPL multipliers. These awards are withheld if any manager’s scoring details are incomplete.
- **Power Rating:** 40% latest GW + 30% last-five average + 20% season average + 10% rank movement over the last five completed GWs. Each component is min–max scaled across league members; when all values tie everyone receives 50 for that component. Final rating is rounded to 0–100. This is relative form, not a probability.

The public FPL API is undocumented and can occasionally be unavailable or change. The site preserves the last successful snapshot and displays its timestamp. It is an independent fan project, not affiliated with the Premier League.

## Price watch

The new Prices page uses **official FPL public data** already included in `bootstrap-static`, with no extra service or subscription:

- Choose a manager to see their last public 15-player squad, actual net price change during the current GW, and the forecast for the next price-change deadline. Private moves since the deadline cannot be seen. After a Free Hit, the last permanent squad is shown and labelled as restored.
- The shared watchlist shows players with **strictly more than 5%** overall ownership who FPL flags as likely or very likely to rise/drop. It uses FPL's likelihood codes (4/5 for rises, -4/-5 for drops), not an invented threshold or probability.
- Price-locked, calibrating or unavailable predictions are labelled and excluded from likely movers. Progress percentages measure progress towards the threshold, **not** a probability of a change.
- Forecasts use `price_change_projections` offset 0 and the matching `price_change_deadlines` timestamp. The FPL forecast timestamp and this site's matchday refresh cadence are displayed. If that forecast deadline has passed, a notice marks it as an old forecast.
- This is a watchlist, not a guaranteed buy/sell recommendation. Price changes are not certain, and our snapshots can lag the official site.

[Official FPL Price Change Predictor explanation](https://www.premierleague.com/en/news/4680462).

## Content Creators

The Content Creators page tracks the 89 creators in [your FPLGameweek list](https://www.fplgameweek.com/#/26/team/61950/league/special_10002), verified on 25 September 2026. The creator roster contains 89 creators. The page also includes all 11 members of our mini-league, giving a combined table of 100 teams; our entries have a subtle green highlight. Creator names and public entry IDs are saved in `content-creators.json`; FPLGameweek is a roster reference, not a runtime data provider. No extra API account, subscription or hosting is used.

Each scheduled update fetches each creator's public entry and history from official FPL. The table has the same columns as Home, with creator name and actual team name, chip badges, rank among all teams in the combined table, net last completed GW score, rank movement within that combined table, calculated FTs and overall FPL rank. Ties use fewer non-chip transfers. Click a creator for their compact details and a public FPL link. Our own manager pop-ups retain mini-league position and show overall FPL rank (OR rank) in place of Power Rating. The combined table never changes the ranks shown on Home or Season. Duplicate entry IDs appear only once.

If one creator request fails after retries, the previous complete creator snapshot is kept, with its own timestamp. It cannot prevent your friends' league from updating. After a season change, creator IDs must be verified and the `season` and `managers` fields in `content-creators.json` updated, because FPL IDs change annually. The roster is not automatically expanded if FPLGameweek adds names mid-season.

Every table header is a button: click once to sort ascending, again for descending. Arrows show the current sort. Missing values stay at the bottom. Sorting does not change the actual rank values or other tables.

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

## Wireless additions

The home hero uses the supplied Ravi Kishan photo with a CSS blur. Money follows includes a decorative falling-rupee animation, a pause button and reduced-motion support. No image generation or paid service is used.

Manager profiles include a team sheet and bench from the latest public GW, plus an official FPL link. Private transfers are never requested. Rank trend starts at GW2: each thin line measures percentage change in overall rank compared with the preceding GW, green above the baseline and red below. The home green/red arrow records use the same percentage comparison, using the latest public overall rank.

Season starts with completed monthly winners. Content Creators has a name/team search; filtering retains positions among the full comparison roster.

## Money follows

Prize rules live in `config.json`: 11 players, ₹5,000 buy-in, ₹55,000 pool; final podium ₹20,000/₹12,000/₹8,000; ten monthly prizes of ₹1,500. Monthly prizes are secured only after all GWs with deadlines in that month are final. Monthly ties split the award equally. Tied final season positions share prizes for occupied places. These tie rules are explicit assumptions and can be changed.

Earned prizes exclude the provisional podium until the season finishes. Net deducts the buy-in. Separate columns show the season prize and net if the season ended at the current standings, without inventing future monthly wins. This tracks prize entitlement, not actual payment or collection. No money is moved by the website.
