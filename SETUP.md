# Setup — MelqueHenrique GitHub profile

1. Back up your existing profile README from `MelqueHenrique/MelqueHenrique`.
2. Copy `README.md`, `assets/`, `scripts/` and `.github/` to the **root** of that public repository.
3. Create a **fine-grained Personal Access Token** at https://github.com/settings/personal-access-tokens/new:
   - Resource owner: your account (`MelqueHenrique`).
   - Repository access: choose **All repositories** to cover your entire portfolio, or **Only select repositories** for a curated set.
   - Repository permissions: **Metadata (read)** and **Contents (read)**. No write permission required on this token.
   - Set an expiration and rotate it before it expires.
   - Depending on policies, access to organization repos may require extra approval and is not implied.
4. In the profile repository go to **Settings → Secrets and variables → Actions → New repository secret**.
   - Name: `GH_STATS_TOKEN`
   - Value: the token you generated. Never commit it to the repository or print it in logs.
5. In **Settings → Actions → General → Workflow permissions**, make sure workflows can use **Read and write permissions** so the separate built-in `GITHUB_TOKEN` can push the updated SVG. If your organization restricts this, use an alternative publishing process.
6. Open **Actions → Update profile stats → Run workflow** to generate the first dashboard.
7. Subsequent scheduled runs take place Mondays at 10:23 UTC. A commit is only created if the generated SVG actually changed. The dashboard uses dates, not run timestamps, so multiple runs on the same day with unchanged totals will not cause commits.

## Accuracy and privacy notes

- Commit and PR metrics use GitHub's **contribution counts** for the *last 365 days*, not every Git commit ever created, and GitHub's contribution eligibility rules apply.
- Repositories displays the count of the non-fork, non-archived owned repositories available to the token. Language percentages aggregate API-reported language **byte counts**, not developer proficiency or time spent.
- For more privacy, select only certain repositories when issuing the token. That changes which repositories are represented by the language and repository count metrics; contributionsCollection may still reflect the authenticated user's other private contributions.
- This project does **not** reveal private repo titles, descriptions, filenames, URLs or source. However, language percentages, repo counts, and contribution numbers themselves become public in the generated SVG; share them only if comfortable.
- The GitHub user token only **reads** private repo metadata and language totals. The GitHub Actions `GITHUB_TOKEN` **writes** the generated SVG to this profile repository. These credentials serve different roles.
- If GitHub reports 403 for a private repo, verify the token's repository access and permissions. If GraphQL returns missing private contributions, consider account/organization privacy settings and GitHub's contribution eligibility behavior.
