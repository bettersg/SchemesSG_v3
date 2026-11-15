import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import SchemeCard from "./scheme-card";
import { makeScheme } from "@/test/fixtures/scheme";
import { I18nWrapper } from "@/test/i18n-wrapper";

const trackMock = vi.hoisted(() => vi.fn());

vi.mock("@/lib/analytics", () => ({
  track: trackMock,
}));

describe("SchemeCard analytics", () => {
  it("sends select_item with index inside items array when clicked with list prop", async () => {
    const user = userEvent.setup();
    const scheme = makeScheme({
      schemeId: "test-scheme",
      schemeName: "Test Scheme",
      agency: "Test Agency",
      schemeType: ["Financial Assistance"],
    });

    render(
      <I18nWrapper>
        <SchemeCard scheme={scheme} list={{ id: "catalog", index: 5 }} />
      </I18nWrapper>,
    );

    const link = screen.getByRole("link", {
      name: /Test Scheme, Test Agency/,
    });

    await user.click(link);

    expect(trackMock).toHaveBeenCalledTimes(1);
    expect(trackMock).toHaveBeenCalledWith("select_item", {
      item_list_id: "catalog",
      items: [
        {
          item_id: "test-scheme",
          item_name: "Test Scheme",
          item_category: "Financial Assistance",
          index: 5,
        },
      ],
    });
  });

  it("does not send analytics when clicked without list prop", async () => {
    const user = userEvent.setup();
    const scheme = makeScheme({
      schemeId: "test-scheme",
      schemeName: "Test Scheme",
      agency: "Test Agency",
    });

    render(
      <I18nWrapper>
        <SchemeCard scheme={scheme} />
      </I18nWrapper>,
    );

    const link = screen.getByRole("link", {
      name: /Test Scheme, Test Agency/,
    });

    await user.click(link);

    expect(trackMock).not.toHaveBeenCalled();
  });
});
