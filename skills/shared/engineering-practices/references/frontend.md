# Frontend practices

## Place components, hooks, and styles

For a new interaction, follow it from the route to the component that owns the edit. Check which pieces need the current entity, draft, or permissions. For example, a billing page with an editable credit limit might grow into this shape as those pieces acquire distinct responsibilities.

```text
src/
  app/                           routes and application providers
  features/billing/
    credit-query.ts              server data used across billing views
    credit-editor/
      credit-editor.tsx          the editor and its public props
      use-credit-draft.ts        draft transitions shared by the editor's controls
      credit-editor.module.css   editor layout in a project using CSS Modules
  shared/ui/dialog/              the shared accessible dialog primitive
  styles/theme.css               application theme entry point
```

Follow the project's naming and styling conventions. Keep a small draft inside the editor until extracting it makes a lifecycle or a set of transitions easier to follow. Place a pure calculation beside its consumer. A hook is useful when the extracted behavior uses React state, subscriptions, or effects. Move a hook up to the feature when several components participate in that feature's workflow. Custom hook calls normally create separate local state for each caller. When controls must edit the *same* draft, create it once in their common owner and pass down values and actions.

Split a component where a consumer can use a clear contract, or where a subtree has a distinct interaction, layout, or subscription. A shared dialog can own focus restoration and dismissal while the billing editor owns save and discard. The dialog should work in another feature without importing billing data or permissions.

## Decide what survives navigation and refresh

| Product behavior | State owner and lifetime |
| --- | --- |
| Users can share a filtered list and use Back to revisit it | Put the relevant filters and page in the route's URL contract. |
| A saved record appears in several views | Let the existing data layer own the server snapshot and its request status. Scope cache identity to the entity, parameters, and access context that affect the response. |
| A user edits an unsaved value | Give the edit session a draft. Decide when switching entities or closing the editor discards it. |
| Several controls show a total calculated from that draft | Calculate the total from the current fields in their common owner. |

For a credit editor, opening account B while a request for A is pending must never populate B with A's values. Key the read and the draft to their respective identities. Accept a result only for its intended identity. Test by resolving B first, then A. If a background refresh arrives while B has a dirty draft, preserve the edits or surface a conflict according to the product contract.

Take a user-triggered action such as Save from its event path. Use an effect when the rendered component needs to stay synchronized with an external resource, such as a subscription. Pair setup with cleanup on identity changes and unmount. For a mutation, closing a dialog or abandoning the response may leave the server operation in progress.

If a save can be retried after an ambiguous outcome, keep its original entity, submitted values, and operation ID together for the supported retry lifetime. Route a late success to that entity's cache. The next editor opened on screen may already belong to another account.

Distinguish the first load, a successful empty result, and a failed request. When refreshing visible data fails, retain the last successful result if it is still valid for this user and entity, and show how to refresh it. For optimistic edits, an earlier failure may arrive after a later edit succeeds. Reconcile the failed edit with the current value, or refetch the authoritative state. Restoring the first edit's entire snapshot can erase the later success.

## Scope CSS and choose tokens

| Decision | Default home |
| --- | --- |
| An editor needs a special grid at narrow widths | Its private stylesheet or the project's component styling mechanism. |
| All densities of a shared control use a configurable gap | A component variable or variant on that control's root. |
| A status color must have the same meaning across products or themes | The design system's semantic token source. |
| The document needs a reset, default font, or top-level theme | The application's global style entry point. |

Check the emitted selector and the rendered DOM. Placing a stylesheet in a component directory gives it a maintainer. Its styling mechanism determines which elements the rules match. When two semantic tokens currently resolve to the same color, decide whether a theme may change them independently before combining them.

For a dialog rendered through a portal, trace the actual portal container's DOM ancestors. An overlay attached under `body` can fall outside a feature's theme root and lose inherited custom property values. Use the project's themed overlay host, mount under the intended theme where clipping and stacking allow it, or explicitly apply the theme at the overlay root. Check the resulting computed styles in the browser with both the page and overlay visible. Also open a dialog in a different theme to detect leakage.

Extend shared controls through their documented variants, state attributes, or styling slots. Introduce a supported variant when multiple consumers need the same presentation. A page selector that depends on the control's internal child order couples unrelated layout changes to the page.

## Verify the interaction that changed

For an editor, exercise opening it by keyboard, saving or recovering from a failure with the draft intact, and returning focus to the intended control. Use the real browser for focus, clipping, inheritance, and layout at realistic content lengths. Select the cases that correspond to the change.

For a slow interaction, trace input through requests, state subscriptions, rendering, and layout. Measure where the delay occurs before changing memoization or splitting a component. Recheck the interaction with the same data and viewport. A lower render count alone does not measure time saved.
