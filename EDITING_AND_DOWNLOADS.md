# Editing and downloading

## Edit a clinic

1. Choose **Edit listing** on its card.
2. Change the public clinic fields; add the public evidence URL and a review note. Intake changes that advertise applications need the original clinic's statement and its location/clinician scope.
3. Select **Review changes**. Compare the before/after values, acknowledge the evidence and type the clinic ID.
4. Approve the draft, copy its edit code, and open secure publishing.
5. Sign into GitHub with repository write access. On **main**, select **Run workflow**, paste into **clinic_edit**, and enter `PUBLISH cNNN` in **confirmation**.
6. Wait for a successful workflow, then refresh the public site.

The browser does not save a clinic change by itself. Closing the editor discards its draft. No GitHub token is requested or stored. GitHub restricts workflow dispatch to repository writers. The save checks stale original values, allowed fields and evidence. Changes are retained in Git history and `data/review_history.json`. Address changes remove the old map point pending a new location review. Undo a published error through another sourced edit or a reviewed Git revert.

## Download a directory

Select **Download directory…**, then choose:

- Current filtered results, manually selected clinics, or all directory listings.
- PDF, Word (.docx), or CSV.

Use **Include in download** on clinic cards to build a custom set. Selections persist while changing filters within the page; refresh clears them. The chooser displays its clinic count and preview before generating a file. Downloads are created locally without uploading data. Public intake notes and source links remain attached. The full verification audit is a separate CSV under the chooser's audit section.
