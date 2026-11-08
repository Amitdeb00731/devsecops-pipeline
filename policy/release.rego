# Phase 5 release gate. This policy is the single, explicit decision that reads the
# evidence from the earlier pipeline stages and decides whether the release may
# proceed. Conftest (Open Policy Agent) evaluates it against gate-input.json, which
# the pipeline assembles from the dynamic test, the Phase 4 signature check and the
# Phase 1 change-approval state. Any deny result fails the policy-gate job, so a
# failing control blocks the release rather than merely being reported on.
package release

import rego.v1

# Block when the dynamic test found a high or critical issue at runtime, such as the
# privileged route being reachable without authorisation.
deny contains msg if {
	input.scans.high_or_critical > 0
	msg := sprintf("release blocked: %d high or critical dynamic finding(s)", [input.scans.high_or_critical])
}

# Block when the release artefact is not signed (the Phase 4 cosign signature).
deny contains msg if {
	not input.artifact.signed
	msg := "release blocked: image is not signed"
}

# Block when the change was not approved by a code owner (the Phase 1 control).
deny contains msg if {
	not input.change.approved
	msg := "release blocked: change not approved by a code owner"
}
