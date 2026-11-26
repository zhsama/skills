# General practices

## Place code with the rule it owns

Start at the smallest scope that can enforce a rule for all its callers. Keep a feature's private types, calculations, tests, and adapters with that feature. Promote a helper when its consumers must agree on the meaning and timing of the operation. Two fields that happen to use the same rounding today can still belong to different domains if their rounding policies can change independently.

Before moving code into a shared directory, name the capability its consumers will import. Check the dependency direction. A shared date formatter can accept a locale as input. Importing the billing store to find the user's locale would give that formatter a billing dependency. Use a package's public entry point across a package boundary. Create another package when a separate consumer, runtime, or release requires that boundary.

## Design an operation from the caller's point of view

Suppose checkout reads available inventory, compares it with the requested quantity, and calls a setter. A second caller can skip the check, and two checkouts can both see the last item. Put the decision in a reservation operation. Give callers the outcomes they need, such as a reservation ID or an insufficient-stock result. Have the inventory owner enforce the decision at the write. A class or wrapper around the existing read and setter would still leave the race.

Start the verification at the public operation. With one item left and two competing requests for it, exactly one reservation should succeed. This example justifies an operation even with a single caller. An extra interface earns its place when it protects such a contract or isolates a dependency that actually varies.

When choosing a dependency, compare the behavior each option would leave the project responsible for. For example, CSV fields can contain delimiters and embedded newlines. Check the project's existing parser against the actual input contract. If a platform API or maintained library already handles the required format, weigh its integration and runtime costs against maintaining that parsing behavior locally.

## Give states and failures distinct meanings

List the cases a caller must handle before choosing a type. For an export job, a running job has an ID, a completed job has an artifact, and a rejected request has a reason. A discriminated union can require those fields in their respective cases. Use an exhaustive branch for internal variants when adding a case requires a caller decision. At an external boundary, validate unknown input and explicitly handle unsupported variants before passing the value inward.

Trace a complicated conditional to the decisions it makes. Independent input checks can return early. A transition with several legal source states belongs with the state owner. A finite protocol often reads clearly as a switch. Check what happens on a new state or a failed operation before replacing any of these with a lookup table or a helper.

Give each catch site a job. A transport adapter can translate a provider error while retaining its cause. A form can preserve the draft and present an actionable rejection. A worker can persist a failed attempt and schedule recovery. Let unexpected failures reach the boundary that can act on them. Use lifecycle cleanup for resources on success, failure, and cancellation. Returning an empty list from a failed read would tell callers that the query succeeded and found zero rows.

## Choose evidence at the boundary

Test the guarantee where it can actually fail. A pure state transition can be exercised directly. A uniqueness guarantee needs competing writes against the storage mechanism. A layout guarantee needs a rendered page. Use a controlled clock or explicit coordination point when order matters. For a performance claim, compare the same workload before and after and name the measured cost.

When a decision changes what other modules may rely on, update the project's authoritative contract and its closest useful check. Keep historical incidents as evidence for the rule. Record project-specific paths, tooling choices, and migration procedures in the project that owns them.
