## 1. Identify removals
- [ ] 1.1 Inventory docs pages that reference unimplemented APIs or speculative features
- [ ] 1.2 Confirm Ditaxis replacements exist for any removed user-facing content

## 2. Remove obsolete pages
- [ ] 2.1 Delete legacy user guide pages that have been replaced by how-to/tutorial/explanation/reference docs
- [ ] 2.2 Delete other obsolete pages (no archive)

## 3. Navigation and links
- [ ] 3.1 Update `docs/mkdocs.yml` nav to remove deleted pages
- [ ] 3.2 Ensure there are no remaining links to deleted pages

## 4. Validation
- [ ] 4.1 Ensure `mkdocs build` succeeds after deletions
- [ ] 4.2 Ensure remaining docs do not contain "future work" / "under development" sections
