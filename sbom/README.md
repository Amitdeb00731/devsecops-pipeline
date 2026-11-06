# Software bills of materials

The retained SBOMs for the application, generated with Syft in CycloneDX format on
each build (Phase 3). An SBOM records what a release contains, so a later-disclosed
vulnerability in a dependency can be traced to the exact builds that shipped it.

- `app-sbom.cdx.json`: the application's SBOM.

See [docs/03-dependencies-sbom.md](../docs/03-dependencies-sbom.md).
