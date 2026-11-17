"use client";

import { Trans } from "@lingui/react/macro";

/** Shown on the detail page of a scheme that was retired without a replacement. */
export function RetiredSchemeNotice() {
  return (
    <div className="w-full rounded-2xl border border-(--schemes-status-info-border) bg-(--schemes-status-info-bg) p-8 text-center">
      <h1 className="mb-3 text-2xl font-semibold text-(--schemes-status-info-text)">
        <Trans>This scheme is no longer listed</Trans>
      </h1>
      <p className="text-sm leading-relaxed text-(--schemes-status-info-text)">
        <Trans>
          This page has been kept so existing links do not break. Browse the
          catalog to find currently listed support schemes.
        </Trans>
      </p>
    </div>
  );
}
